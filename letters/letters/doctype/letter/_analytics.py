from __future__ import annotations

import frappe


class AnalyticsMixin:
    def get_analytics(self):
        frappe.has_permission("Letter", "read", doc=self, throw=True)
        name = self.name
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

        latest = sends[0]
        total   = latest.total_recipients or 0
        sent    = latest.sent_count or 0
        opened  = frappe.db.count("Email Send Recipient", {"parent": latest.name, "opened": 1})
        last_opened = frappe.db.get_value(
            "Email Send Recipient",
            {"parent": latest.name, "opened": 1},
            "opened_on", order_by="opened_on desc",
        )
        unsubscribed = frappe.db.count(
            "Email Unsubscribe",
            {"reference_doctype": "Letter", "reference_name": name},
        )
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
            "Email Send", {"campaign": self.name}, "name", order_by="creation desc"
        )
        if not send:
            return []
        return frappe.get_all(
            "Email Send Recipient",
            filters={"parent": send},
            fields=["email", "status", "opened", "opened_on"],
            order_by="email asc",
            limit=int(limit),
        )

    def get_send_progress(self):
        frappe.has_permission("Letter", "read", doc=self, throw=True)
        name = self.name
        statuses = ["Sending", "Sent", "Failed", "Partial"]
        if not frappe.db.exists("Email Send", {"campaign": name, "status": ["in", statuses]}):
            return {"status": "Queued", "sent": 0, "total": 0}
        send = frappe.get_last_doc(
            "Email Send",
            filters={"campaign": name, "status": ["in", statuses]},
            order_by="creation desc",
        )
        return {
            "status": send.status,
            "sent":   send.sent_count or 0,
            "total":  send.total_recipients or 0,
        }

    def record_open(self, email):
        from letters.letters.api.sending import _record_open
        _record_open(self.name, email)
