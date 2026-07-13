from __future__ import annotations

import json

import frappe
from frappe import _


class SendingMixin:
    def send_test_email(self, recipient=None, subject=None, preview_text=None, email_width=None):
        """Compile blocks and send a test email to `recipient` (defaults to session user)."""
        frappe.has_permission("Letter", "read", doc=self, throw=True)
        html = self.render_preview_html(
            preview_text=preview_text if preview_text is not None else self.preview_text,
            email_width=email_width,
        )
        subj = subject or self.subject

        # A test send has no triggering document, but Frappe still runs the
        # message (and subject) through Jinja before mailing it — an
        # unresolved `{{ doc.field }}` merge tag (left over from a
        # notification-linked Letter) would otherwise crash the send with
        # "'doc' is undefined". Fill in real values from a sample record
        # where we can, then neutralize anything left so it can't reach Jinja.
        from letters.letters.api.notifications import (
            neutralize_unresolved_merge_tags, resolve_merge_tags_for_preview,
        )
        html = neutralize_unresolved_merge_tags(resolve_merge_tags_for_preview(html, self.name))
        if subj:
            subj = neutralize_unresolved_merge_tags(resolve_merge_tags_for_preview(subj, self.name))

        requested = (recipient or "").strip()
        email = requested or frappe.session.user
        if not frappe.utils.validate_email_address(email, throw=False):
            frappe.throw(_("{0} is not a valid email address.").format(email))

        frappe.sendmail(
            recipients=[email],
            subject=f"[TEST] {subj or 'Email Preview'}",
            message=html,
            now=False,
            # Our compiler already produces a complete, inline-styled HTML doc.
            # raw_html keeps it intact (our <style> stays in <head>, where Gmail
            # reads media queries — Frappe's default wrapper moves it into <body>,
            # so Gmail ignores it). add_css skips Frappe's email CSS, which made
            # Gmail drop all embedded styles. Both are needed for the responsive
            # layout to survive to Gmail. See email_compiler.
            add_css=False,
            raw_html=True,
        )
        return {"sent_to": email}

    def schedule(self, scheduled_at: str):
        """Mark this letter to be sent at `scheduled_at` (ISO-8601, server timezone)."""
        frappe.has_permission("Letter", "write", doc=self, throw=True)
        from letters.letters.api.recipients import _has_recipient_config

        if self.status in ("Sent", "Sending"):
            frappe.throw(_("This letter has already been sent or is currently sending."))
        if not self.blocks_json:
            frappe.throw(_("Letter has no content to send."))
        if not self.subject:
            frappe.throw(_("Letter has no subject line."))

        if not _has_recipient_config(self):
            frappe.throw(_("Choose recipients before scheduling this letter."))

        dt = frappe.utils.get_datetime(scheduled_at)
        if dt <= frappe.utils.now_datetime():
            frappe.throw(_("Scheduled time must be in the future."))

        self.db_set("scheduled_at", dt)
        self.db_set("status", "Scheduled")
        frappe.db.commit()
        return {"scheduled_at": str(dt)}

    def send(self, email_group=None, recipients=None, doctype_config=None):
        """
        Compile and send this letter to the given audience.

        Pass one of:
          - email_group:    name of a Frappe Email Group (respects unsubscribes)
          - recipients:     JSON string or list of email addresses
          - doctype_config: JSON string/dict with keys: doctype, email_field, filters
          - (none):         fall back to the letter's saved recipient_config

        The per-recipient loop is enqueued as a background job so large lists
        don't block the web request.
        """
        frappe.has_permission("Letter", "write", doc=self, throw=True)
        from letters.letters.api.recipients import (
            _has_recipient_config, _load_recipient_config,
            _recipient_args_from_config, _resolve_multi_source,
            _suppressed_emails, _valid_emails,
        )
        from letters.letters.api.sending import (
            MAX_RECIPIENTS, _bulk_insert_recipients, _enqueue_send, _resume_send,
        )

        if not self.blocks_json:
            frappe.throw(_("Letter has no content to send."))
        if not self.subject:
            frappe.throw(_("Letter has no subject line."))

        # Resume a prior partial/failed send instead of starting over
        existing = frappe.get_all(
            "Email Send",
            filters={"letter": self.name},
            fields=["name", "status"],
            order_by="creation desc",
            limit=1,
        )
        if existing and existing[0].status in ("Failed", "Partial"):
            return _resume_send(existing[0].name, self.name, self)

        # Atomically claim the send: transition Draft/Scheduled → Sending only if
        # the letter is still in a sendable state. rowcount==0 means another
        # request beat us to it (race condition) or the letter is already sent.
        letter_qb = frappe.qb.DocType("Letter")
        (
            frappe.qb.update(letter_qb)
            .set(letter_qb.status, "Sending")
            .where(
                (letter_qb.name == self.name)
                & (letter_qb.status.isin(["Draft", "Scheduled"]))
            )
        ).run()
        claimed = frappe.db._cursor.rowcount
        frappe.db.commit()
        if not claimed:
            frappe.throw(_("This letter has already been sent or is currently sending."))
        self.status = "Sending"

        try:
            # ── Resolve recipients ─────────────────────────────────────────────────
            # When explicit args are passed (legacy / direct API call) use them.
            # Otherwise read from the letter's saved recipient_config, which may be
            # the new multi-source array format or the old single-source object.
            # Scope suppression to this specific letter (+ its folder + global).
            suppressed_fn = lambda: _suppressed_emails(self.name)

            email_group = email_group  # local alias; may stay None
            if email_group or doctype_config or recipients:
                # Explicit args — route through the legacy single-source resolver
                recipient_list, email_group, mode, invalid_emails = _resolve_recipients(
                    email_group, recipients, doctype_config, MAX_RECIPIENTS,
                    suppressed_fn, _valid_emails,
                )
            else:
                sources = _load_recipient_config(self)
                if not sources:
                    frappe.throw(_("This letter has no saved recipients. Open it and choose an audience before sending."))

                if len(sources) == 1:
                    # Single source — use the legacy path so email_group mode is preserved
                    src = sources[0]
                    eg  = src.get("email_group") if src.get("type") == "group" else None
                    dc  = {k: src[k] for k in ("doctype", "email_field", "filters") if k in src} if src.get("type") == "doctype" else None
                    rc  = src.get("recipients") if src.get("type") == "paste" else None
                    recipient_list, email_group, mode, invalid_emails = _resolve_recipients(
                        eg, rc, dc, MAX_RECIPIENTS, suppressed_fn, _valid_emails,
                    )
                else:
                    # Multi-source array — merge, dedup, validate
                    recipient_list, invalid_emails = _resolve_multi_source(
                        sources, MAX_RECIPIENTS, suppressed_fn, _valid_emails,
                        letter_name=self.name,
                    )
                    email_group = None
                    mode = "direct"

            # Snapshot the content at send time so edits after clicking Send can't
            # change what recipients receive. _execute_send reads from the snapshot.
            # total_recipients/sent_count only ever count the valid, queued
            # list — invalid addresses never reach the Email Queue, so counting
            # them here would make get_send_progress wait forever for a queue
            # count that can never arrive.
            send_doc = frappe.get_doc({
                "doctype": "Email Send",
                "letter": self.name,
                "status": "Sending",
                "send_mode": mode,
                "email_group": email_group or "",
                "total_recipients": len(recipient_list),
                "sent_count": 0,
                "snapshot_subject":      self.subject,
                "snapshot_preview_text": self.preview_text or "",
                "snapshot_email_width":  getattr(self, "email_width", None) or 600,
                "snapshot_blocks":       self.blocks_json,
                "include_unsubscribe":   1 if getattr(self, "include_unsubscribe", False) else 0,
            })
            send_doc.insert(ignore_permissions=True)
            _bulk_insert_recipients(send_doc.name, recipient_list, status="Pending")
            if invalid_emails:
                _bulk_insert_recipients(
                    send_doc.name, invalid_emails, status="Invalid", start_idx=len(recipient_list) + 1,
                )
            frappe.db.commit()

            _enqueue_send(send_doc.name, self.name)
            return {"queued": True, "count": len(recipient_list), "mode": mode, "skipped_invalid": len(invalid_emails)}

        except Exception:
            frappe.db.set_value("Letter", self.name, "status", "Draft", update_modified=False)
            self.status = "Draft"
            frappe.db.commit()
            raise


def _resolve_recipients(email_group, recipients, doctype_config, max_recipients, suppressed_fn, valid_fn):
    """Resolve the final recipient list from whichever source was provided.

    Returns (recipient_list, email_group, mode, invalid_emails).
    Throws on empty or oversized results so the caller gets a clear error.
    """
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
        cfg       = json.loads(doctype_config) if isinstance(doctype_config, str) else doctype_config
        dt        = cfg.get("doctype")
        email_fld = cfg.get("email_field")
        filters   = cfg.get("filters") or {}
        if not dt or not email_fld:
            frappe.throw(_("doctype_config must include doctype and email_field."))
        frappe.has_permission(dt, "read", throw=True)
        filters[email_fld] = ["!=", ""]
        rows = frappe.get_all(dt, filters=filters, fields=[email_fld], limit=max_recipients + 1)
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

    suppressed = suppressed_fn()
    if suppressed:
        recipient_list = [e for e in recipient_list if e not in suppressed]
    if not recipient_list:
        frappe.throw(_("All selected recipients have unsubscribed from this letter."))

    recipient_list, invalid_emails = valid_fn(recipient_list)
    if not recipient_list:
        frappe.throw(_("No valid email addresses to send to."))

    if len(recipient_list) > max_recipients:
        frappe.throw(_(
            "This audience has more than {0} recipients, which is above the "
            "per-letter limit. Narrow your filters or split the send."
        ).format(max_recipients))

    return recipient_list, email_group, mode, invalid_emails
