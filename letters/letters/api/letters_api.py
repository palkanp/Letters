from __future__ import annotations

import json

import frappe
from frappe import _

from .recipients import _normalize_recipient_config
from ..doctype.letter._content import _unique_letter_title


def _sync_subject_to_notification(letter_name: str, subject: str):
    """Update the linked Notification's subject if it differs from the letter's subject."""
    row = frappe.db.sql(
        "SELECT name, subject FROM `tabNotification` WHERE letter = %s LIMIT 1",
        letter_name,
        as_dict=True,
    )
    if row and row[0].get("subject") != subject:
        frappe.db.set_value("Notification", row[0]["name"], "subject", subject)


@frappe.whitelist(methods=["GET", "POST"])
def get_letter(name: str):
    doc = frappe.get_doc("Letter", name)
    frappe.has_permission("Letter", "read", doc=doc, throw=True)
    return doc.as_builder_dict()


@frappe.whitelist(methods=["POST"])
def save_letter(name: str | None = None, title: str | None = None, subject: str | None = None, preview_text: str | None = None, blocks: str | None = None, email_width: int | None = None, canvas_background: str | None = None, recipient_config: str | None = None, folder: str | None = None, include_unsubscribe: bool | None = None):
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
        if folder is not None:
            doc.folder = folder
        if include_unsubscribe is not None:
            doc.include_unsubscribe = 1 if include_unsubscribe else 0
        doc.blocks_json = blocks_json
        doc.save()
        if subject is not None and doc.subject:
            _sync_subject_to_notification(doc.name, doc.subject)
    else:
        frappe.has_permission("Letter", "create", throw=True)
        doc = frappe.get_doc({
            "doctype": "Letter",
            "title": _unique_letter_title(title or "Untitled Letter"),
            "subject": subject or "",
            "preview_text": preview_text or "",
            "status": "Draft",
            "email_width": int(email_width) if email_width else 600,
            "canvas_background": canvas_background or "#ffffff",
            "blocks_json": blocks_json,
            "recipient_config": normalized_config or "",
            "folder": folder or "",
            "include_unsubscribe": 1 if include_unsubscribe else 0,
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

    def _first_bg(blocks_data):
        """Return the first explicit background-color in the block tree (depth-first)."""
        stack = list(blocks_data)
        while stack:
            node = stack.pop(0)
            bg = (node.get("props") or {}).get("background_color", "")
            if bg and bg != "transparent":
                return bg
            stack[:0] = node.get("children", [])
        return "#ffffff"

    if name and not blocks:
        doc = frappe.get_doc("Letter", name)
        frappe.has_permission("Letter", "read", doc=doc, throw=True)
        try:
            html = doc.render_preview_html(preview_text=preview_text, email_width=email_width)
            blocks_data = json.loads(doc.blocks_json or "[]")
            return {"html": html, "first_bg": _first_bg(blocks_data)}
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Letters render_preview error")
            frappe.throw(str(e))
    else:
        blocks_data = blocks if isinstance(blocks, list) else json.loads(blocks or "[]")
        try:
            compiler = EmailCompiler(blocks_data, preview_text=preview_text or "", email_width=email_width or 600)
            return {"html": compiler.compile(), "first_bg": _first_bg(blocks_data)}
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Letters render_preview error")
            frappe.throw(str(e))


@frappe.whitelist(methods=["GET", "POST"])
def get_letters(folder: str | None = None):
    """Return Letter records for the dashboard, excluding those used as notification templates."""
    frappe.has_permission("Letter", "read", throw=True)
    from frappe.query_builder import DocType

    Letter = DocType("Letter")
    Notification = DocType("Notification")

    linked = (
        frappe.qb.from_(Notification)
        .select(Notification.letter)
        .where(Notification.letter.isnotnull())
        .where(Notification.letter != "")
    )

    q = (
        frappe.qb.from_(Letter)
        .select(
            Letter.name, Letter.title, Letter.status, Letter.subject,
            Letter.modified, Letter.creation, Letter.owner, Letter.folder,
        )
        .where(Letter.name.notin(linked))
        .orderby(Letter.modified, order=frappe.qb.desc)
        .limit(200)
    )

    if folder:
        q = q.where(Letter.folder == folder)

    return q.run(as_dict=True)


@frappe.whitelist(methods=["POST"])
def duplicate_letter(name: str):
    """Create an exact copy of a letter as a new Draft."""
    original = frappe.get_doc("Letter", name)
    frappe.has_permission("Letter", "read", doc=original, throw=True)
    return original.duplicate()
