from __future__ import annotations

import json

import frappe
from frappe import _

from .recipients import _normalize_recipient_config
from ..doctype.letter._content import _unique_letter_title


@frappe.whitelist(methods=["GET", "POST"])
def get_campaign(name: str):
    doc = frappe.get_doc("Letter", name)
    frappe.has_permission("Letter", "read", doc=doc, throw=True)
    return doc.as_builder_dict()


@frappe.whitelist(methods=["POST"])
def save_campaign(name: str | None = None, title: str | None = None, subject: str | None = None, preview_text: str | None = None, blocks: str | None = None, email_width: int | None = None, canvas_background: str | None = None, recipient_config: str | None = None):
    blocks_json = json.dumps(blocks if isinstance(blocks, list) else json.loads(blocks or "[]"))
    normalized_config = _normalize_recipient_config(recipient_config)

    if name:
        doc = frappe.get_doc("Letter", name)
        frappe.has_permission("Letter", "write", doc=doc, throw=True)
        if title is not None:
            doc.title = title
        if subject is not None:
            doc.subject = subject
        if preview_text is not None:
            doc.preview_text = preview_text
        if email_width is not None:
            try:
                doc.email_width = int(email_width)
            except (AttributeError, TypeError, ValueError):
                pass
        if canvas_background is not None:
            doc.canvas_background = canvas_background
        if normalized_config is not None:
            doc.recipient_config = normalized_config
        doc.blocks_json = blocks_json
        doc.save()
    else:
        frappe.has_permission("Letter", "create", throw=True)
        doc = frappe.get_doc({
            "doctype": "Letter",
            "title": _unique_letter_title(title or "Untitled Letter"),
            "subject": subject or "",
            "preview_text": preview_text or "",
            "status": "Draft",
            "email_width": int(email_width) if email_width else 600,
            "canvas_background": canvas_background or "#f3f4f6",
            "blocks_json": blocks_json,
            "recipient_config": normalized_config or "",
        })
        doc.insert()

    return {"name": doc.name, "title": doc.title, "status": doc.status}


@frappe.whitelist(methods=["GET", "POST"])
def get_templates():
    """Return all active Letters Templates with rendered preview HTML for the picker."""
    from letters.letters.utils.email_compiler import EmailCompiler

    templates = frappe.get_all(
        "Letters Template",
        filters={"is_active": 1},
        fields=["name", "title", "thumbnail", "blocks_json", "sort_order"],
        order_by="sort_order asc, title asc",
    )
    for tpl in templates:
        blocks_data = json.loads(tpl.get("blocks_json") or "[]")
        try:
            compiler = EmailCompiler(blocks_data, preview_text="", email_width=600)
            tpl["preview_html"] = compiler.compile()
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Letters template preview error")
            tpl["preview_html"] = ""
    return templates


@frappe.whitelist(methods=["GET", "POST"])
def render_preview(name: str | None = None, blocks: str | None = None, preview_text: str | None = None, email_width: int | None = None):
    """Compile blocks to email-safe HTML."""
    from letters.letters.utils.email_compiler import EmailCompiler

    if name and not blocks:
        doc = frappe.get_doc("Letter", name)
        frappe.has_permission("Letter", "read", doc=doc, throw=True)
        try:
            html = doc.render_preview_html(preview_text=preview_text, email_width=email_width)
            return {"html": html}
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Letters render_preview error")
            frappe.throw(str(e))
    else:
        blocks_data = blocks if isinstance(blocks, list) else json.loads(blocks or "[]")
        try:
            compiler = EmailCompiler(blocks_data, preview_text=preview_text or "", email_width=email_width or 600)
            return {"html": compiler.compile()}
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Letters render_preview error")
            frappe.throw(str(e))


@frappe.whitelist(methods=["POST"])
def duplicate_campaign(name: str):
    """Create an exact copy of a campaign as a new Draft."""
    original = frappe.get_doc("Letter", name)
    frappe.has_permission("Letter", "read", doc=original, throw=True)
    return original.duplicate()
