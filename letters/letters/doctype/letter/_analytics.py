from __future__ import annotations

import frappe


class AnalyticsMixin:
    def get_analytics(self):
        frappe.has_permission("Letter", "read", doc=self, throw=True)
        name = self.name
        sends = frappe.get_all(
            "Email Send",
            filters={"letter": name},
            fields=["name", "status", "total_recipients", "sent_count", "creation"],
            order_by="creation desc",
        )
        if not sends:
            return {
                "sent_status": None, "total": 0, "sent": 0, "opened": 0,
                "open_rate": 0, "last_opened": None, "last_sent": None,
            }

        latest = sends[0]
        total   = latest.total_recipients or 0
        sent    = latest.sent_count or 0
        opened  = frappe.db.count("Email Send Recipient", {"parent": latest.name, "opened": 1})
        last_opened = frappe.db.get_value(
            "Email Send Recipient",
            {"parent": latest.name, "opened": 1},
            "opened_on", order_by="opened_on desc",
        )
        # A recipient counts as unsubscribed if they opted out globally, or opted
        # out of this letter's own folder (category-level opt-out) — Letters never
        # writes an Email Unsubscribe row scoped to reference_doctype="Letter"
        # itself, so that filter would always read zero.
        recipient_emails = frappe.get_all(
            "Email Send Recipient", filters={"parent": latest.name}, pluck="email"
        )
        unsubscribed = 0
        if recipient_emails:
            folder = frappe.db.get_value("Letter", name, "folder")
            or_filters = [{"global_unsubscribe": 1}]
            if folder:
                or_filters.append({"reference_doctype": "Letter Category", "reference_name": folder})
            unsubscribed_emails = frappe.get_all(
                "Email Unsubscribe",
                filters={"email": ["in", recipient_emails]},
                or_filters=or_filters,
                pluck="email",
                distinct=True,
            )
            unsubscribed = len(unsubscribed_emails)
        status_counts = {}
        for row in frappe.get_all("Email Send Recipient", filters={"parent": latest.name}, fields=["status"]):
            s = row.status or "Pending"
            status_counts[s] = status_counts.get(s, 0) + 1

        return {
            "sent_status":   latest.status,
            "total":         total,
            "sent":          sent,
            "opened":        opened,
            "open_rate":     round((opened / sent) * 100, 1) if sent else 0,
            "unsubscribed":  unsubscribed,
            "last_opened":   str(last_opened) if last_opened else None,
            "last_sent":     str(latest.creation),
            "status_counts": status_counts,
        }

    def get_recipients(self, limit=200):
        frappe.has_permission("Letter", "read", doc=self, throw=True)
        send = frappe.db.get_value(
            "Email Send", {"letter": self.name}, "name", order_by="creation desc"
        )
        if not send:
            return []
        sent = frappe.get_all(
            "Email Send Recipient",
            filters={"parent": send},
            fields=["email", "status", "opened", "opened_on"],
            order_by="email asc",
            limit=int(limit),
        )

        # Email Send Recipient.status only means "accepted into the Email
        # Queue" (set at queue time, see _execute_send) — it does not reflect
        # actual SMTP delivery. Real per-recipient outcome lives on core's
        # Email Queue (queue_separately creates one row per recipient), so
        # overlay that here and attach the Email Queue row name for failures
        # so the UI can link straight to its error history.
        delivery = self._recipient_delivery_status()
        for row in sent:
            info = delivery.get(row.email.lower())
            if not info:
                continue
            if info["status"] == "Error":
                row.status = "Failed"
                row.email_queue = info["name"]
            elif info["status"] == "Sent":
                row.status = "Sent"

        # Also surface emails that were suppressed for this letter (unsubscribed).
        # These were never inserted into Email Send Recipient, so we look them up
        # from Email Unsubscribe scoped to this letter + its folder.
        or_filters = [{"reference_doctype": "Letter", "reference_name": self.name}]
        folder = frappe.db.get_value("Letter", self.name, "folder")
        if folder:
            or_filters.append({"reference_doctype": "Letter Category", "reference_name": folder})

        suppressed_rows = frappe.get_all(
            "Email Unsubscribe",
            or_filters=or_filters,
            fields=["email"],
            distinct=True,
        )
        sent_emails = {r.email for r in sent}
        excluded = [
            frappe._dict(email=r.email, status="Excluded", opened=0, opened_on=None)
            for r in suppressed_rows
            if r.email not in sent_emails
        ]
        return sent + excluded

    def _recipient_delivery_status(self):
        """Map lowercased recipient email -> {status, name} from core's Email
        Queue for this letter. `name` is the Email Queue row, used to link a
        failed recipient to its full error history (a row can accumulate
        multiple Error Log entries across retries, so only the row name is
        useful here — not a single error text snapshot).
        """
        EQ = frappe.qb.DocType("Email Queue")
        EQR = frappe.qb.DocType("Email Queue Recipient")
        rows = (
            frappe.qb.from_(EQ)
            .join(EQR).on(EQR.parent == EQ.name)
            .select(EQR.recipient, EQ.status, EQ.name)
            .where((EQ.reference_doctype == "Letter") & (EQ.reference_name == self.name))
        ).run(as_dict=True)
        return {r.recipient.lower(): {"status": r.status, "name": r.name} for r in rows}

    def get_send_progress(self):
        frappe.has_permission("Letter", "read", doc=self, throw=True)
        from letters.letters.api.sending import _reconcile_send_status

        name = self.name
        statuses = ["Sending", "Sent", "Failed", "Partial"]
        send = frappe.get_all(
            "Email Send",
            filters={"letter": name, "status": ["in", statuses]},
            fields=["name", "status", "sent_count", "total_recipients"],
            order_by="creation desc",
            limit=1,
        )
        if not send:
            return {"status": "Queued", "sent": 0, "delivered": 0, "failed": 0, "total": 0}
        send = send[0]
        # Live delivered/failed counts come off core's Email Queue; this also
        # settles the letter's terminal status once delivery has drained.
        return _reconcile_send_status(
            name, send.name, send.total_recipients or 0, send.status, send.sent_count or 0,
        )

    def record_open(self, email):
        from letters.letters.api.sending import _record_open
        _record_open(self.name, email)
