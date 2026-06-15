import frappe
from frappe.model.document import Document

from ._analytics import AnalyticsMixin
from ._content import ContentMixin
from ._sending import SendingMixin


class Letter(ContentMixin, SendingMixin, AnalyticsMixin, Document):
    def validate(self):
        if self.is_new():
            return
        if self.status == "Sending" and self.has_value_changed("title"):
            frappe.throw(
                frappe._("Cannot rename a campaign while it is actively sending."),
                frappe.ValidationError,
            )
