from __future__ import annotations

import json

import frappe
from frappe import _


class ContentMixin:
    def as_builder_dict(self):
        frappe.has_permission("Letter", "read", doc=self, throw=True)
        from letters.letters.api.recipients import _load_recipient_config

        return {
            "name": self.name,
            "title": self.title,
            "subject": self.subject,
            "preview_text": self.preview_text or "",
            "status": self.status,
            "scheduled_at": str(self.scheduled_at) if self.scheduled_at else None,
            "email_width": getattr(self, "email_width", None) or 600,
            "canvas_background": getattr(self, "canvas_background", None) or "#ffffff",
            "blocks": json.loads(self.blocks_json) if self.blocks_json else [],
            "recipient_config": _load_recipient_config(self),
        }

    def render_preview_html(self, preview_text=None, email_width=None):
        from letters.letters.utils.email_compiler import EmailCompiler

        pt = preview_text if preview_text is not None else (self.preview_text or "")
        ew = int(email_width) if email_width else (getattr(self, "email_width", None) or 600)
        compiler = EmailCompiler(self.blocks_json or "[]", preview_text=pt, email_width=ew)
        return compiler.compile()

    def duplicate(self):
        frappe.has_permission("Letter", "create", throw=True)
        new_doc = frappe.get_doc({
            "doctype": "Letter",
            "title": _unique_letter_title(f"Copy of {self.title}"),
            "subject": self.subject or "",
            "preview_text": self.preview_text or "",
            "status": "Draft",
            "email_width": getattr(self, "email_width", None) or 600,
            "blocks_json": self.blocks_json or "[]",
            "recipient_config": getattr(self, "recipient_config", None) or "",
        })
        new_doc.insert()
        return {"name": new_doc.name, "title": new_doc.title}


def _unique_letter_title(base):
    """Return a title that doesn't collide with an existing Letter title."""
    base = (base or "Untitled Letter").strip() or "Untitled Letter"
    existing = frappe.db.get_all("Letter", filters={"title": ["like", f"{base}%"]}, pluck="title")
    if base not in existing:
        return base
    n = 1
    while f"{base} - {n}" in existing:
        n += 1
    return f"{base} - {n}"
