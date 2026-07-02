from __future__ import annotations

import frappe
from frappe.email.doctype.notification.notification import Notification


class LettersNotification(Notification):
    """Extends Frappe's Notification to use a visual Letter as the email body.

    When a Notification document has its `letter` custom field set, the
    Letter's compiled HTML is used instead of the `message` field.  Any
    Jinja expressions written in the Letter's text blocks (e.g.
    ``{{ doc.customer_name }}``) are resolved against the standard Frappe
    notification context at send time.
    """

    def validate(self):
        super().validate()
        if getattr(self, "letter", None):
            self._validate_letter_unique()

    def _validate_letter_unique(self):
        existing = frappe.db.get_value(
            "Notification",
            {"letter": self.letter, "name": ("!=", self.name or "")},
            "name",
        )
        if existing:
            frappe.throw(
                frappe._(
                    "Letter {0} is already linked to Notification {1}. "
                    "Each Letter can only be linked to one Notification."
                ).format(self.letter, existing),
                frappe.ValidationError,
            )

    def send_an_email(self, doc, context):
        if getattr(self, "letter_message_type", None) == "Letter Builder" and getattr(self, "letter", None):
            original_message = self.message
            try:
                self.message = self._compile_letter()
                super().send_an_email(doc, context)
            finally:
                self.message = original_message
        else:
            super().send_an_email(doc, context)

    def _compile_letter(self) -> str:
        import json

        from letters.letters.utils.email_compiler import EmailCompiler

        letter = frappe.get_doc("Letter", self.letter)
        blocks = json.loads(letter.blocks_json or "[]")
        compiler = EmailCompiler(
            blocks,
            preview_text=letter.preview_text or "",
            email_width=letter.email_width or 600,
        )
        return compiler.compile()
