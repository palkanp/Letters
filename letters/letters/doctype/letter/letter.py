import frappe
from frappe.model.document import Document

from ._analytics import AnalyticsMixin
from ._content import ContentMixin
from ._sending import SendingMixin


def get_permission_query_conditions(user=None):
    return (
        "`tabLetter`.`name` NOT IN ("
        "SELECT `letter` FROM `tabNotification` "
        "WHERE `letter` IS NOT NULL AND `letter` != ''"
        ")"
    )


class Letter(ContentMixin, SendingMixin, AnalyticsMixin, Document):
    def validate(self):
        if self.is_new():
            return
        if self.status == "Sending" and self.has_value_changed("title"):
            frappe.throw(
                frappe._("Cannot rename a letter while it is actively sending."),
                frappe.ValidationError,
            )

    def after_save(self):
        if not self.subject:
            return
        row = frappe.db.sql(
            "SELECT name, subject FROM `tabNotification` WHERE letter = %s LIMIT 1",
            self.name,
            as_dict=True,
        )
        if row and row[0].get("subject") != self.subject:
            frappe.db.set_value("Notification", row[0]["name"], "subject", self.subject)
