from __future__ import annotations

import frappe
from frappe import _

from .recipients import _recipient_args_from_config, _suppressed_emails, _valid_emails


# Hard ceiling on a single campaign's audience. Above this we refuse the send
# with a clear message rather than silently dropping recipients.
MAX_RECIPIENTS = 50000

# Background send-job timeout in seconds.
SEND_JOB_TIMEOUT = 600


@frappe.whitelist(methods=["POST"])
def send_test(blocks: str | None = None, subject: str | None = None, preview_text: str | None = None, name: str | None = None, recipient: str | None = None, email_width: int | None = None):
    """Send a test email to the given recipient (defaults to the logged-in user)."""
    if name and not blocks:
        doc = frappe.get_doc("Letter", name)
        frappe.has_permission("Letter", "read", doc=doc, throw=True)
        return doc.send_test_email(
            recipient=recipient,
            subject=subject,
            preview_text=preview_text,
            email_width=email_width,
        )

    # Blocks passed directly (preview mode without a saved campaign)
    from letters.letters.utils.email_compiler import EmailCompiler

    blocks_data = blocks if isinstance(blocks, list) else __import__("json").loads(blocks or "[]")
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

    frappe.sendmail(
        recipients=[email],
        subject=f"[TEST] {subject or 'Email Preview'}",
        message=html,
        now=False,
    )
    return {"sent_to": email}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def track_open(recipient_email: str | None = None, reference_name: str | None = None, reference_doctype: str | None = None, **kwargs):
    """Tracking-pixel endpoint: record an email open, then return a 1×1 gif."""
    from frappe.utils.verified_command import verify_request

    try:
        if frappe.in_test or verify_request():
            if reference_doctype == "Letter" and reference_name and recipient_email:
                _record_open(reference_name, recipient_email)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Letters track_open error")

    frappe.response.update(frappe.utils.get_imaginary_pixel_response())


@frappe.whitelist(methods=["GET", "POST"])
def get_letter_analytics(name: str):
    """Open-rate analytics for a letter, aggregated over its recipient rows."""
    doc = frappe.get_doc("Letter", name)
    frappe.has_permission("Letter", "read", doc=doc, throw=True)
    return doc.get_analytics()


@frappe.whitelist(methods=["GET", "POST"])
def get_letter_recipients(name: str, limit: int = 200):
    """Return the list of recipients for the most recent send of a letter."""
    doc = frappe.get_doc("Letter", name)
    frappe.has_permission("Letter", "read", doc=doc, throw=True)
    return doc.get_recipients(limit=limit)


@frappe.whitelist(methods=["GET", "POST"])
def get_send_progress(name: str):
    """Return live send progress for a letter (polled from the frontend)."""
    doc = frappe.get_doc("Letter", name)
    frappe.has_permission("Letter", "read", doc=doc, throw=True)
    return doc.get_send_progress()


@frappe.whitelist(methods=["POST"])
def schedule_letter(name: str, scheduled_at: str):
    """Mark a letter to be sent at a future datetime (ISO-8601 string, server timezone)."""
    doc = frappe.get_doc("Letter", name)
    frappe.has_permission("Letter", "write", doc=doc, throw=True)
    if frappe.db.exists("Notification", {"letter": name}):
        frappe.throw("This letter is linked to a Notification and cannot be sent as a campaign.")
    return doc.schedule(scheduled_at)


@frappe.whitelist(methods=["POST"])
def send_letter(name: str, recipients: str | None = None, email_group: str | None = None, doctype_config: str | None = None):
    """
    Compile and send a letter.

    Pass one of:
      - email_group:    name of a Frappe Email Group (respects unsubscribes)
      - recipients:     JSON string or list of email addresses
      - doctype_config: JSON string/dict with keys: doctype, email_field, filters
    """
    doc = frappe.get_doc("Letter", name)
    frappe.has_permission("Letter", "write", doc=doc, throw=True)
    if frappe.db.exists("Notification", {"letter": name}):
        frappe.throw("This letter is linked to a Notification and cannot be sent as a campaign.")
    if doc.status == "Sent":
        frappe.throw(_("This letter has already been sent."), exc=frappe.ValidationError)
    if doc.status == "Sending":
        frappe.throw(_("This letter is currently sending."), exc=frappe.ValidationError)
    return doc.send(email_group=email_group, recipients=recipients, doctype_config=doctype_config)


@frappe.whitelist(methods=["POST"])
def resume_send(name: str):
    """
    Recover a send that has stopped making progress.

    Covers two cases:
      - status is Failed/Partial: re-enqueue the whole delivery loop as usual.
      - status is Sending but stalled (e.g. a worker/queue restart dropped the
        background jobs that fan recipients out to Email Queue): find whichever
        recipients never got an Email Queue row and re-queue just those, without
        starting the send over or double-sending anyone.
    """
    doc = frappe.get_doc("Letter", name)
    frappe.has_permission("Letter", "write", doc=doc, throw=True)

    send = frappe.get_all(
        "Email Send",
        filters={"letter": name},
        fields=["name", "status", "snapshot_subject", "snapshot_preview_text",
                 "snapshot_email_width", "snapshot_blocks", "include_unsubscribe", "send_mode"],
        order_by="creation desc",
        limit=1,
    )
    if not send:
        frappe.throw(_("No send found for this letter."))
    send = send[0]

    if send.status in ("Failed", "Partial"):
        return _resume_send(send.name, name, doc)

    if send.status != "Sending":
        frappe.throw(_("This letter isn't in a resumable state."))

    all_emails = frappe.get_all("Email Send Recipient", filters={"parent": send.name}, pluck="email")
    queued_emails = {
        r[0] for r in frappe.db.sql(
            """
            select qr.recipient from `tabEmail Queue Recipient` qr
            join `tabEmail Queue` q on q.name = qr.parent
            where q.reference_doctype = 'Letter' and q.reference_name = %s
            """,
            (name,),
        )
    }
    missing = [e for e in all_emails if e not in queued_emails]
    if not missing:
        frappe.throw(_("This send has no missing recipients — it may just be slow. Check back shortly."))

    from letters.letters.utils.email_compiler import EmailCompiler
    compiler = EmailCompiler(
        send.snapshot_blocks or "",
        preview_text=send.snapshot_preview_text or "",
        email_width=send.snapshot_email_width or 600,
    )
    html = compiler.compile()
    send_doc = frappe.get_doc("Email Send", send.name)
    _queue_recipients(send_doc, name, missing, send.snapshot_subject or "", html)
    frappe.db.commit()
    return {"resumed": True, "requeued": len(missing)}


def process_scheduled_sends():
    """Scheduled task: fire any letters whose scheduled_at has passed."""
    from frappe.utils import now_datetime

    due = frappe.get_all(
        "Letter",
        filters={"status": "Scheduled", "scheduled_at": ["<=", now_datetime()]},
        fields=["name"],
    )
    for row in due:
        try:
            letter = frappe.qb.DocType("Letter")
            (
                frappe.qb.update(letter)
                .set(letter.status, "Draft")
                .where((letter.name == row.name) & (letter.status == "Scheduled"))
            ).run()
            claimed = frappe.db._cursor.rowcount
            frappe.db.commit()
            if not claimed:
                continue
            letter_owner = frappe.db.get_value("Letter", row.name, "owner")
            frappe.set_user(letter_owner or frappe.session.user)
            try:
                send_letter(row.name)
            finally:
                frappe.set_user("Administrator")
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Letters scheduled send error: {row.name}")
            try:
                frappe.db.set_value("Letter", row.name, "status", "Failed")
                frappe.db.commit()
            except Exception:
                frappe.log_error(frappe.get_traceback(), f"Letters scheduled send cleanup error: {row.name}")


# ── Private helpers (not whitelist; used by doc methods and _execute_send) ───

def _record_open(letter_name, email):
    """Mark recipient rows for `email` as opened; increment open_count."""
    sends = frappe.get_all("Email Send", filters={"letter": letter_name}, pluck="name")
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


def _resume_send(send_doc_name, letter_name, letter_doc):
    """Re-enqueue a partial/failed Email Send."""
    unsent = frappe.db.count(
        "Email Send Recipient",
        {"parent": send_doc_name, "status": ["!=", "Sent"]},
    )
    frappe.db.set_value("Email Send", send_doc_name, "status", "Sending")
    letter_doc.status = "Sending"
    letter_doc.save(ignore_permissions=True)
    frappe.db.commit()
    _enqueue_send(send_doc_name, letter_name)
    return {"queued": True, "count": unsent, "resumed": True}


def _bulk_insert_recipients(send_doc_name, recipient_list):
    """Write child rows for an Email Send in one batched INSERT."""
    now  = frappe.utils.now()
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


def _enqueue_send(send_doc_name, letter_name):
    """Enqueue the per-recipient delivery loop as a background job."""
    frappe.enqueue(
        "letters.letters.api._execute_send",
        queue="long",
        timeout=SEND_JOB_TIMEOUT,
        job_name=f"letters_send_{letter_name}",
        send_doc_name=send_doc_name,
        letter_name=letter_name,
    )


def _execute_send(send_doc_name, letter_name):
    """
    Background job: compile the letter once and hand the whole recipient list to
    Frappe's Email Queue in a single bulk call.

    queue_separately=True lets the framework fan the list out into per-recipient
    Email Queue rows across parallel background jobs (reusing one SMTP connection
    per 1000-recipient batch), instead of this job looping frappe.sendmail once
    per recipient. send_priority=0 keeps a large campaign from starving
    transactional mail. Delivery, retry, and stuck-job recovery are then owned by
    core's Email Queue.

    Recipients already marked Sent are skipped so a retry only re-queues the
    remainder. Must NOT be decorated with @frappe.whitelist().
    """
    try:
        send_doc = frappe.get_doc("Email Send", send_doc_name)

        # Use the content snapshot taken at queue time so edits made after
        # clicking Send don't affect what recipients receive.
        blocks_json   = send_doc.snapshot_blocks or ""
        subject       = send_doc.snapshot_subject or ""
        preview_text  = send_doc.snapshot_preview_text or ""
        email_width   = send_doc.snapshot_email_width or 600

        # Fall back to live letter for sends queued before snapshot was introduced
        if not blocks_json:
            doc         = frappe.get_doc("Letter", letter_name)
            blocks_json = doc.blocks_json
            subject     = subject or doc.subject
            preview_text = preview_text or doc.preview_text or ""
            email_width  = email_width or getattr(doc, "email_width", None) or 600

        from letters.letters.utils.email_compiler import EmailCompiler
        compiler = EmailCompiler(blocks_json, preview_text=preview_text, email_width=email_width)
        html = compiler.compile()

        pending = [row.email for row in send_doc.recipients if row.status != "Sent"]
        if pending:
            _queue_recipients(send_doc, letter_name, pending, subject, html)
            # queue_separately hands each address to the Email Queue. Mark the
            # rows queued — this "Sent" means "accepted into the Email Queue".
            # Actual per-recipient delivery is tracked live off the Email Queue
            # (see _delivery_counts / get_send_progress).
            frappe.db.sql(
                "update `tabEmail Send Recipient` set status='Sent' "
                "where parent=%s and status!='Sent'",
                send_doc_name,
            )

        # Stay in "Sending": the letter is now delivering. get_send_progress and
        # the reconcile_active_sends scheduled task settle it to a terminal
        # status once core's Email Queue has drained.
        frappe.db.set_value(
            "Email Send", send_doc_name,
            {"status": "Sending", "sent_count": len(send_doc.recipients)},
            update_modified=False,
        )
        frappe.db.set_value(
            "Letter", letter_name, "status", "Sending",
            update_modified=False,
        )
        frappe.db.commit()

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Letters _execute_send error")
        try:
            frappe.db.set_value("Email Send", send_doc_name, "status", "Failed")
            frappe.db.set_value("Letter", letter_name, "status", "Failed")
            recipient = frappe.qb.DocType("Email Send Recipient")
            (
                frappe.qb.update(recipient)
                .set(recipient.status, "Failed")
                .where((recipient.parent == send_doc_name) & (recipient.status != "Sent"))
            ).run()
            frappe.db.commit()
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Letters _execute_send cleanup error")


def _queue_recipients(send_doc, letter_name, emails, subject, html):
    """Hand the full recipient list to core's Email Queue in one bulk call.

    The framework builds the message once, then batches the addresses into
    parallel per-recipient sends (see frappe.email.doctype.email_queue).
    """
    include_unsub = bool(send_doc.include_unsubscribe)
    # Email-group sends use Frappe's native unsubscribe (sets Email Group
    # Member.unsubscribed). All other sends use a custom portal page that lets
    # recipients manage folder-level or global opt-outs.
    if send_doc.send_mode == "email_group":
        unsubscribe_method = None
    elif include_unsub:
        unsubscribe_method = "/api/method/letters.letters.api.unsubscribe.unsubscribe_redirect"
    else:
        unsubscribe_method = None

    frappe.sendmail(
        recipients=emails,
        subject=subject,
        message=html,
        now=False,
        queue_separately=True,
        send_priority=0,
        reference_doctype="Letter",
        reference_name=letter_name,
        unsubscribe_method=unsubscribe_method,
        unsubscribe_message=_("Unsubscribe") if include_unsub else None,
        add_unsubscribe_link=1 if include_unsub else 0,
        email_read_tracker_url="/api/method/letters.letters.api.track_open",
    )


def _delivery_counts(letter_name):
    """Live delivery tally from core's Email Queue for this letter.

    queue_separately creates one Email Queue row per recipient, tagged with
    reference_doctype=Letter, so grouping by status gives real SMTP progress.
    Returns None when no rows exist (send just starting, or logs cleared).
    """
    # Aggregate via frappe.qb — recent Frappe rejects raw "count(name) as c"
    # field strings passed to get_all for SQL-injection safety.
    from frappe.query_builder.functions import Count

    EQ = frappe.qb.DocType("Email Queue")
    rows = (
        frappe.qb.from_(EQ)
        .select(EQ.status, Count(EQ.name).as_("c"))
        .where((EQ.reference_doctype == "Letter") & (EQ.reference_name == letter_name))
        .groupby(EQ.status)
    ).run(as_dict=True)
    if not rows:
        return None
    counts    = {r.status: r.c for r in rows}
    queued    = sum(counts.values())
    delivered = counts.get("Sent", 0)
    failed    = counts.get("Error", 0)
    return {
        "delivered": delivered,
        "failed":    failed,
        "queued":    queued,
        "pending":   queued - delivered - failed,
    }


def _reconcile_send_status(letter_name, send_name, total, current_status, queued_count):
    """Compute live delivery progress from the Email Queue and, once the queue
    has drained, persist the terminal status. Returns a progress dict shaped for
    the frontend: {status, sent (accepted), delivered, failed, total}.
    """
    counts = _delivery_counts(letter_name)

    # No live Email Queue rows (old send whose logs were cleared): trust the
    # stored status; treat the queued count as delivered for terminal states.
    if not counts:
        delivered = queued_count if current_status in ("Sent", "Partial") else 0
        return {"status": current_status, "sent": queued_count,
                "delivered": delivered, "failed": 0, "total": total}

    delivered, failed, pending = counts["delivered"], counts["failed"], counts["pending"]

    # Still draining (rows pending, or the framework hasn't queued them all yet).
    if pending > 0 or (total and counts["queued"] < total):
        return {"status": "Sending", "sent": queued_count,
                "delivered": delivered, "failed": failed, "total": total}

    # Drained — settle the terminal status once.
    terminal = "Sent" if failed == 0 else ("Failed" if delivered == 0 else "Partial")
    if current_status != terminal:
        frappe.db.set_value("Email Send", send_name,
                            {"status": terminal, "sent_count": delivered}, update_modified=False)
        frappe.db.set_value("Letter", letter_name, "status", terminal, update_modified=False)
        frappe.db.commit()
    return {"status": terminal, "sent": queued_count,
            "delivered": delivered, "failed": failed, "total": total}


def reconcile_active_sends():
    """Scheduled fallback: settle Letters stuck in 'Sending' once their Email
    Queue has drained, for sends nobody is actively polling in the builder."""
    from frappe.utils import add_to_date, now_datetime

    for letter_name in frappe.get_all("Letter", filters={"status": "Sending"}, pluck="name"):
        try:
            sends = frappe.get_all(
                "Email Send",
                filters={"letter": letter_name, "status": ["in", ["Sending", "Sent", "Failed", "Partial"]]},
                fields=["name", "status", "sent_count", "total_recipients", "creation"],
                order_by="creation desc", limit=1,
            )
            if not sends:
                continue
            send = sends[0]
            res = _reconcile_send_status(
                letter_name, send.name, send.total_recipients or 0, send.status, send.sent_count or 0,
            )
            # Staleness guard: a send with no live queue rows that has been
            # "Sending" for over 30 minutes has almost certainly delivered and
            # had its Email Queue logs cleared — settle it as Sent.
            if res["status"] == "Sending" and _delivery_counts(letter_name) is None:
                if send.creation and send.creation < add_to_date(now_datetime(), minutes=-30):
                    frappe.db.set_value("Email Send", send.name, "status", "Sent", update_modified=False)
                    frappe.db.set_value("Letter", letter_name, "status", "Sent", update_modified=False)
                    frappe.db.commit()
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Letters reconcile_active_sends error: {letter_name}")
