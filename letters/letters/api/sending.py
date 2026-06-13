from __future__ import annotations

import json

import frappe
from frappe import _

from .recipients import _recipient_args_from_config, _suppressed_emails, _valid_emails



# Hard ceiling on a single campaign's audience. Above this we refuse the send
# with a clear message rather than silently dropping recipients. Tune as needed
# for your sending infrastructure.
MAX_RECIPIENTS = 50000



# Background send-job timeout in seconds.
SEND_JOB_TIMEOUT = 600



# Flush per-recipient progress to the DB every N sends so a worker crash mid-batch
# loses at most this many recipients' tracked status (they'd resend on retry).
COMMIT_EVERY = 100




@frappe.whitelist(methods=["POST"])
def send_test(blocks: str | None = None, subject: str | None = None, preview_text: str | None = None, name: str | None = None, recipient: str | None = None, email_width: int | None = None):
    """Send a test email to the given recipient (defaults to the logged-in user)."""
    from letters.letters.utils.email_compiler import EmailCompiler

    if name and not blocks:
        doc = frappe.get_doc("Letters Campaign", name)
        frappe.has_permission("Letters Campaign", "read", doc=doc, throw=True)
        blocks_data = doc.blocks_json or "[]"
        subject = subject or doc.subject
        preview_text = preview_text or doc.preview_text
        if email_width is None:
            email_width = getattr(doc, "email_width", None) or 600
    else:
        blocks_data = blocks if isinstance(blocks, list) else json.loads(blocks or "[]")

    try:
        compiler = EmailCompiler(blocks_data, preview_text=preview_text or "", email_width=email_width or 600)
        html = compiler.compile()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Letters send_test compile error")
        frappe.throw(str(e))

    session_email = frappe.session.user
    requested = (recipient or "").strip()
    if requested and requested != session_email:
        frappe.throw(_("Test emails can only be sent to your own account ({0}).").format(session_email))
    email = session_email
    if not frappe.utils.validate_email_address(email, throw=False):
        frappe.throw(_("Your account does not have a valid email address."))
    test_subject = f"[TEST] {subject or 'Email Preview'}"

    # Queue rather than send inline (now=False): a slow SMTP server must not
    # block the web request. The email queue worker delivers it shortly.
    frappe.sendmail(
        recipients=[email],
        subject=test_subject,
        message=html,
        now=False,
    )
    return {"sent_to": email}




# ── Open tracking & analytics ─────────────────────────────────────────────────

@frappe.whitelist(allow_guest=True, methods=["GET"])
def track_open(recipient_email: str | None = None, reference_name: str | None = None, reference_doctype: str | None = None, **kwargs):
    """Tracking-pixel endpoint: record an email open, then return a 1x1 gif.

    Frappe's email queue generates and *signs* this URL (via email_read_tracker_url),
    so we verify the signature before trusting the params. A pixel is always
    returned, even on failure, so the email never shows a broken image. Opens
    only register when the site is publicly reachable.
    """
    from frappe.utils.verified_command import verify_request

    try:
        if frappe.in_test or verify_request():
            if reference_doctype == "Letters Campaign" and reference_name and recipient_email:
                _record_open(reference_name, recipient_email)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Letters track_open error")

    frappe.response.update(frappe.utils.get_imaginary_pixel_response())




def _record_open(campaign_name, email):
    """Mark this campaign's recipient row(s) for `email` as opened. First open
    stamps opened_on; every hit increments open_count."""
    sends = frappe.get_all("Email Send", filters={"campaign": campaign_name}, pluck="name")
    if not sends:
        return
    rows = frappe.get_all(
        "Email Send Recipient",
        filters={"parent": ["in", sends], "email": email},
        fields=["name", "opened", "open_count"],
    )
    for r in rows:
        update = {"open_count": (r.open_count or 0) + 1}
        if not r.opened:
            update["opened"] = 1
            update["opened_on"] = frappe.utils.now_datetime()
        frappe.db.set_value("Email Send Recipient", r.name, update, update_modified=False)
    frappe.db.commit()




@frappe.whitelist(methods=["GET", "POST"])
def get_campaign_analytics(name: str):
    """Open-rate analytics for a campaign, aggregated over its recipient rows."""
    doc = frappe.get_doc("Letters Campaign", name)
    frappe.has_permission("Letters Campaign", "read", doc=doc, throw=True)

    sends = frappe.get_all(
        "Email Send",
        filters={"campaign": name},
        fields=["name", "status", "total_recipients", "sent_count", "creation"],
        order_by="creation desc",
    )
    if not sends:
        return {
            "sent_status": None, "total": 0, "sent": 0, "opened": 0,
            "open_rate": 0, "last_opened": None, "last_sent": None,
        }

    send_names = [s.name for s in sends]
    # Metrics are scoped to the most recent send so open_rate has a stable denominator.
    # Aggregating across resends produces rates >100% and a misleading denominator.
    latest_send = sends[0]
    total = latest_send.total_recipients or 0
    sent  = latest_send.sent_count or 0
    opened = frappe.db.count(
        "Email Send Recipient", {"parent": latest_send.name, "opened": 1}
    )
    last_opened = frappe.db.get_value(
        "Email Send Recipient",
        {"parent": latest_send.name, "opened": 1},
        "opened_on", order_by="opened_on desc",
    )
    unsubscribed = frappe.db.count(
        "Email Unsubscribe",
        {"reference_doctype": "Letters Campaign", "reference_name": name},
    )
    # Per-recipient status breakdown from the most recent send
    status_counts = {}
    for row in frappe.get_all(
        "Email Send Recipient",
        filters={"parent": latest_send.name},
        fields=["status"],
    ):
        s = row.status or "Pending"
        status_counts[s] = status_counts.get(s, 0) + 1

    return {
        "sent_status":  sends[0].status,
        "total":        total,
        "sent":         sent,
        "opened":       opened,
        "open_rate":    round((opened / sent) * 100, 1) if sent else 0,
        "unsubscribed": unsubscribed,
        "last_opened":  str(last_opened) if last_opened else None,
        "last_sent":    str(sends[0].creation),
        "status_counts": status_counts,
    }




@frappe.whitelist(methods=["GET", "POST"])
def get_campaign_recipients(name: str, limit: int = 200):
    """Return the list of recipients for the most recent send of a campaign."""
    doc = frappe.get_doc("Letters Campaign", name)
    frappe.has_permission("Letters Campaign", "read", doc=doc, throw=True)

    send = frappe.db.get_value(
        "Email Send", {"campaign": name}, "name", order_by="creation desc"
    )
    if not send:
        return []

    rows = frappe.get_all(
        "Email Send Recipient",
        filters={"parent": send},
        fields=["email", "status", "opened", "opened_on"],
        order_by="email asc",
        limit=int(limit),
    )
    return rows




@frappe.whitelist(methods=["GET", "POST"])
def get_send_progress(name: str):
    """Return live send progress for a campaign (polls from the frontend)."""
    doc = frappe.get_doc("Letters Campaign", name)
    frappe.has_permission("Letters Campaign", "read", doc=doc, throw=True)

    send = frappe.get_last_doc(
        "Email Send",
        filters={"campaign": name, "status": ["in", ["Sending", "Sent", "Failed", "Partial"]]},
        order_by="creation desc",
    ) if frappe.db.exists("Email Send", {"campaign": name, "status": ["in", ["Sending", "Sent", "Failed", "Partial"]]}) else None

    if not send:
        return {"status": "Queued", "sent": 0, "total": 0}

    return {
        "status": send.status,
        "sent": send.sent_count or 0,
        "total": send.total_recipients or 0,
    }




@frappe.whitelist(methods=["POST"])
def schedule_campaign(name: str, scheduled_at: str):
    """Mark a campaign to be sent at a future datetime (ISO-8601 string, server timezone)."""
    doc = frappe.get_doc("Letters Campaign", name)
    frappe.has_permission("Letters Campaign", "write", doc=doc, throw=True)

    if doc.status in ("Sent", "Sending"):
        frappe.throw(_("This campaign has already been sent or is currently sending."))

    if not doc.blocks_json:
        frappe.throw(_("Campaign has no content to send."))
    if not doc.subject:
        frappe.throw(_("Campaign has no subject line."))

    # A scheduled send runs with no UI present, so the audience must already be
    # saved on the campaign — otherwise the send would silently have no one to
    # go to when it fires.
    recip = _recipient_args_from_config(doc)
    if not any(recip):
        frappe.throw(_("Choose recipients before scheduling this campaign."))

    from frappe.utils import get_datetime
    dt = get_datetime(scheduled_at)
    if dt <= frappe.utils.now_datetime():
        frappe.throw(_("Scheduled time must be in the future."))

    doc.db_set("scheduled_at", dt)
    doc.db_set("status", "Scheduled")
    frappe.db.commit()
    return {"scheduled_at": str(dt)}




@frappe.whitelist(methods=["POST"])
def send_campaign(name: str, recipients: str | None = None, email_group: str | None = None, doctype_config: str | None = None):
    """
    Compile and send a campaign.

    Pass one of:
      - email_group:    name of a Frappe Email Group (respects unsubscribes)
      - recipients:     JSON string or list of email addresses
      - doctype_config: JSON string/dict with keys:
                          doctype, email_field, filters (dict of frappe filter expressions)

    The actual per-recipient loop is enqueued as a background job so large lists
    do not block the web request or risk a gunicorn timeout.
    """
    doc = frappe.get_doc("Letters Campaign", name)
    frappe.has_permission("Letters Campaign", "write", doc=doc, throw=True)

    # Idempotency guard — a fully-sent or in-flight campaign cannot be re-sent.
    if doc.status in ("Sent", "Sending"):
        frappe.throw(_("This campaign has already been sent or is currently sending."))

    if not doc.blocks_json:
        frappe.throw(_("Campaign has no content to send."))
    if not doc.subject:
        frappe.throw(_("Campaign has no subject line."))

    # ── Resume a previous partial/failed send instead of starting over ───────
    # Per-recipient state lives on the Email Send doc, so a retry re-runs the
    # same job; _execute_send skips recipients already marked Sent. This is what
    # prevents a failed batch from re-delivering to everyone on retry.
    existing = frappe.get_all(
        "Email Send",
        filters={"campaign": name},
        fields=["name", "status"],
        order_by="creation desc",
        limit=1,
    )
    if existing and existing[0].status in ("Failed", "Partial"):
        return _resume_send(existing[0].name, name, doc)

    # ── Fall back to the campaign's saved audience when no explicit source ───
    # is passed. Scheduled sends (process_scheduled_sends) and any server-side
    # caller rely on this: the recipient selection is persisted on the campaign
    # so the send no longer depends on transient UI state.
    if not (email_group or doctype_config or recipients):
        recipients, email_group, doctype_config = _recipient_args_from_config(doc)
        if not (email_group or doctype_config or recipients):
            frappe.throw(_("This campaign has no saved recipients. Open it and choose an audience before sending."))

    # ── Resolve recipient list synchronously so we can fail fast ─────────────
    if email_group:
        members = frappe.get_all(
            "Email Group Member",
            filters={"email_group": email_group, "unsubscribed": 0},
            fields=["email"],
        )
        recipient_list = [m.email for m in members if m.email]
        if not recipient_list:
            frappe.throw(_("The selected Email Group has no active subscribers."))
        mode = "email_group"
    elif doctype_config:
        cfg = json.loads(doctype_config) if isinstance(doctype_config, str) else doctype_config
        dt         = cfg.get("doctype")
        email_fld  = cfg.get("email_field")
        filters    = cfg.get("filters") or {}
        if not dt or not email_fld:
            frappe.throw(_("doctype_config must include doctype and email_field."))
        frappe.has_permission(dt, "read", throw=True)
        filters[email_fld] = ["!=", ""]
        # Fetch one past the cap so we can detect (and reject) an oversized
        # audience instead of silently truncating it.
        rows = frappe.get_all(dt, filters=filters, fields=[email_fld], limit=MAX_RECIPIENTS + 1)
        recipient_list = [r.get(email_fld, "").strip() for r in rows if r.get(email_fld, "").strip()]
        if not recipient_list:
            frappe.throw(_("No records match the selected filters."))
        email_group = None
        mode = "direct"
    else:
        if isinstance(recipients, str):
            recipients = json.loads(recipients)
        recipient_list = [r.strip() for r in (recipients or []) if r.strip()]
        if not recipient_list:
            frappe.throw(_("No recipients provided."))
        email_group = None
        mode = "direct"

    # ── Honour unsubscribes before sending ───────────────────────────────────
    suppressed = _suppressed_emails()
    if suppressed:
        recipient_list = [e for e in recipient_list if e not in suppressed]
    if not recipient_list:
        frappe.throw(_("All selected recipients have unsubscribed from this campaign."))

    # ── Drop malformed addresses (server-side, regardless of client) ─────────
    recipient_list, invalid_count = _valid_emails(recipient_list)
    if not recipient_list:
        frappe.throw(_("No valid email addresses to send to."))

    # ── Guard against an oversized audience (no silent truncation) ───────────
    if len(recipient_list) > MAX_RECIPIENTS:
        frappe.throw(_(
            "This audience has more than {0} recipients, which is above the "
            "per-campaign limit. Narrow your filters or split the send."
        ).format(MAX_RECIPIENTS))

    # ── Claim the send synchronously to prevent a race between two requests ──
    # Each recipient becomes a child row with its own status, so the background
    # job (and any later retry) can track delivery per address. The parent is
    # inserted empty (cheap) and the child rows are written with a single bulk
    # INSERT — a per-row ORM insert of a large audience would otherwise run for
    # minutes inside the web request and trip the gunicorn worker timeout.
    send_doc = frappe.get_doc({
        "doctype": "Email Send",
        "campaign": name,
        "status": "Sending",
        "send_mode": mode,
        "email_group": email_group or "",
        "total_recipients": len(recipient_list),
        "sent_count": 0,
    })
    send_doc.insert(ignore_permissions=True)
    _bulk_insert_recipients(send_doc.name, recipient_list)
    frappe.db.commit()  # flush so the background job can read the send_doc

    # Mark campaign as Sending before returning so any re-submit attempt is blocked
    doc.status = "Sending"
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    _enqueue_send(send_doc.name, name)
    return {
        "queued": True,
        "count": len(recipient_list),
        "mode": mode,
        "skipped_invalid": invalid_count,
    }




def _resume_send(send_doc_name, campaign_name, campaign_doc):
    """Re-enqueue a partial/failed Email Send. Only its unsent recipients will
    be (re)attempted, so retrying never re-delivers to addresses already Sent."""
    unsent = frappe.db.count(
        "Email Send Recipient",
        {"parent": send_doc_name, "status": ["!=", "Sent"]},
    )
    frappe.db.set_value("Email Send", send_doc_name, "status", "Sending")
    campaign_doc.status = "Sending"
    campaign_doc.save(ignore_permissions=True)
    frappe.db.commit()

    _enqueue_send(send_doc_name, campaign_name)
    return {"queued": True, "count": unsent, "resumed": True}




def _bulk_insert_recipients(send_doc_name, recipient_list):
    """Write the per-recipient child rows for an Email Send in one batched
    INSERT instead of an ORM insert per address.

    For a large audience the ORM path (Document with N child rows) issues N
    individual INSERTs and validates each — minutes of work that, run inside
    the synchronous web request, exceeds the gunicorn worker timeout. A single
    chunked bulk INSERT keeps the request bounded regardless of audience size.
    The rows land Pending, exactly as the ORM path produced them, so resume and
    progress tracking are unchanged."""
    now = frappe.utils.now()
    user = frappe.session.user
    fields = [
        "name", "creation", "modified", "modified_by", "owner", "docstatus",
        "idx", "parent", "parentfield", "parenttype", "email", "status",
    ]
    values = [
        (
            frappe.generate_hash(length=10), now, now, user, user, 0,
            idx + 1, send_doc_name, "recipients", "Email Send", email, "Pending",
        )
        for idx, email in enumerate(recipient_list)
    ]
    frappe.db.bulk_insert("Email Send Recipient", fields=fields, values=values)




def _enqueue_send(send_doc_name, campaign_name):
    """Enqueue the per-recipient delivery loop as a background job."""
    frappe.enqueue(
        "letters.letters.api._execute_send",
        queue="long",
        timeout=SEND_JOB_TIMEOUT,
        job_name=f"letters_send_{campaign_name}",
        send_doc_name=send_doc_name,
        campaign_name=campaign_name,
    )




def _execute_send(send_doc_name, campaign_name):
    """
    Background job: compile the campaign and send one email per recipient,
    recording delivery status on each recipient row. Recipients already marked
    Sent are skipped, so a retry resumes from where a previous run stopped.

    Runs in a worker process; must NOT be decorated with @frappe.whitelist().
    """
    try:
        doc = frappe.get_doc("Letters Campaign", campaign_name)
        send_doc = frappe.get_doc("Email Send", send_doc_name)

        from letters.letters.utils.email_compiler import EmailCompiler
        compiler = EmailCompiler(doc.blocks_json, preview_text=doc.preview_text, email_width=getattr(doc, "email_width", None) or 600)
        html = compiler.compile()

        sent = failed = 0
        for idx, row in enumerate(send_doc.recipients):
            if row.status == "Sent":
                sent += 1
                continue

            try:
                # Setting a reference doc makes Frappe inject a signed
                # unsubscribe footer (with a guest confirmation page) and
                # auto-suppress Email Unsubscribe matches — for every send mode,
                # not just Email Groups. Recipients already opted out were
                # filtered in send_campaign via _suppressed_emails().
                frappe.sendmail(
                    recipients=[row.email],
                    subject=doc.subject,
                    message=html,
                    now=False,
                    reference_doctype="Letters Campaign",
                    reference_name=campaign_name,
                    # Frappe injects a per-recipient tracking pixel pointing here
                    # (with signed recipient_email/reference params) so opens can
                    # be recorded. Only registers when the site is publicly
                    # reachable — a localhost pixel never loads.
                    email_read_tracker_url="/api/method/letters.letters.api.track_open",
                )
                row.status = "Sent"
                frappe.db.set_value(
                    "Email Send Recipient", row.name, "status", "Sent",
                    update_modified=False,
                )
                sent += 1
            except Exception as e:
                row.status = "Failed"
                frappe.db.set_value(
                    "Email Send Recipient", row.name,
                    {"status": "Failed", "error_message": str(e)[:500]},  # full trace in Error Log
                    update_modified=False,
                )
                failed += 1
                frappe.log_error(frappe.get_traceback(), "Letters recipient send error")

            # Periodically flush so a worker crash doesn't lose progress.
            if (idx + 1) % COMMIT_EVERY == 0:
                frappe.db.commit()

        # ── Finalise: derive the batch outcome from per-recipient results ────
        if failed == 0:
            send_status = campaign_status = "Sent"
        elif sent == 0:
            send_status = campaign_status = "Failed"
        else:
            send_status, campaign_status = "Partial", "Partial"

        # Persist the parent fields directly instead of send_doc.save(): the
        # per-recipient statuses were already written via set_value, so a full
        # save would needlessly rewrite the entire (up to MAX_RECIPIENTS) child
        # table a second time.
        frappe.db.set_value(
            "Email Send", send_doc_name,
            {"status": send_status, "sent_count": sent},
            update_modified=False,
        )
        frappe.db.set_value(
            "Letters Campaign", campaign_name, "status", campaign_status,
            update_modified=False,
        )
        frappe.db.commit()

    except Exception:
        # A failure here is the whole batch (e.g. compile error), not one
        # recipient. Mark Failed (not Draft) so a retry resumes rather than
        # re-delivering to everyone.
        frappe.log_error(frappe.get_traceback(), "Letters _execute_send error")
        try:
            frappe.db.set_value("Email Send", send_doc_name, "status", "Failed")
            frappe.db.set_value("Letters Campaign", campaign_name, "status", "Failed")
            # Mark all Pending rows as Failed so they don't show misleadingly in
            # the recipient list after a batch-level error (e.g. compile failure).
            frappe.db.sql(
                "UPDATE `tabEmail Send Recipient` SET status = 'Failed'"
                " WHERE parent = %s AND status = 'Pending'",
                send_doc_name,
            )
            frappe.db.commit()
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Letters _execute_send cleanup error")




def process_scheduled_sends():
    """Scheduled task: fire any campaigns whose scheduled_at has passed."""
    from frappe.utils import now_datetime
    due = frappe.get_all(
        "Letters Campaign",
        filters={"status": "Scheduled", "scheduled_at": ["<=", now_datetime()]},
        fields=["name"],
    )
    for row in due:
        try:
            # Atomic claim: only the worker that flips Scheduled -> Draft wins.
            # Concurrent workers reading the same due list will find status no
            # longer "Scheduled" and claim nothing, preventing duplicate sends.
            claimed = frappe.db.sql(
                "UPDATE `tabLetters Campaign` SET status = 'Draft'"
                " WHERE name = %s AND status = 'Scheduled'",
                row.name,
            )
            frappe.db.commit()
            if not claimed:
                continue
            # Run the send as the campaign's owner so recipient rows are attributed
            # to them rather than "Administrator" (the typical scheduler user).
            campaign_owner = frappe.db.get_value("Letters Campaign", row.name, "owner")
            frappe.set_user(campaign_owner or frappe.session.user)
            try:
                send_campaign(row.name)
            finally:
                frappe.set_user("Administrator")
        except Exception:
            # The send didn't start (e.g. no saved recipients, compile error).
            # Mark Failed rather than leaving it silently reverted to Draft, so
            # the failure is visible and the user can fix and retry.
            frappe.log_error(frappe.get_traceback(), f"Letters scheduled send error: {row.name}")
            try:
                frappe.db.set_value("Letters Campaign", row.name, "status", "Failed")
                frappe.db.commit()
            except Exception:
                frappe.log_error(frappe.get_traceback(), f"Letters scheduled send cleanup error: {row.name}")
