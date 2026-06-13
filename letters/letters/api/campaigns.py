from __future__ import annotations

import json

import frappe
from frappe import _

from .recipients import _load_recipient_config, _normalize_recipient_config




@frappe.whitelist(methods=["GET", "POST"])
def get_campaign(name: str):
    doc = frappe.get_doc("Letters Campaign", name)
    frappe.has_permission("Letters Campaign", "read", doc=doc, throw=True)
    return {
        "name": doc.name,
        "title": doc.title,
        "subject": doc.subject,
        "preview_text": doc.preview_text or "",
        "status": doc.status,
        "scheduled_at": str(doc.scheduled_at) if doc.scheduled_at else None,
        "email_width": getattr(doc, "email_width", None) or 600,
        "blocks": json.loads(doc.blocks_json) if doc.blocks_json else [],
        "recipient_config": _load_recipient_config(doc),
    }




def _unique_campaign_title(base):
    """Return a campaign title that doesn't collide with an existing record.

    Campaigns are autonamed `field:title`, so two campaigns can't share a title.
    If ``base`` is taken we append ` - 1`, ` - 2`, … until we find a free slot.
    """
    base = (base or "Untitled Campaign").strip() or "Untitled Campaign"
    if not frappe.db.exists("Letters Campaign", base):
        return base
    n = 1
    while frappe.db.exists("Letters Campaign", f"{base} - {n}"):
        n += 1
    return f"{base} - {n}"




@frappe.whitelist(methods=["POST"])
def save_campaign(name: str | None = None, title: str | None = None, subject: str | None = None, preview_text: str | None = None, blocks: str | None = None, email_width: int | None = None, recipient_config: str | None = None):
    blocks_json = json.dumps(blocks if isinstance(blocks, list) else json.loads(blocks or "[]"))
    normalized_config = _normalize_recipient_config(recipient_config)

    if name:
        doc = frappe.get_doc("Letters Campaign", name)
        frappe.has_permission("Letters Campaign", "write", doc=doc, throw=True)
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
        if normalized_config is not None:
            doc.recipient_config = normalized_config
        doc.blocks_json = blocks_json
        doc.save()
    else:
        frappe.has_permission("Letters Campaign", "create", throw=True)
        doc = frappe.get_doc({
            "doctype": "Letters Campaign",
            "title": _unique_campaign_title(title or "Untitled Campaign"),
            "subject": subject or "",
            "preview_text": preview_text or "",
            "status": "Draft",
            "email_width": int(email_width) if email_width else 600,
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
        doc = frappe.get_doc("Letters Campaign", name)
        frappe.has_permission("Letters Campaign", "read", doc=doc, throw=True)
        blocks_data = doc.blocks_json or "[]"
        if preview_text is None:
            preview_text = doc.preview_text
        if email_width is None:
            email_width = getattr(doc, "email_width", None) or 600
    else:
        blocks_data = blocks if isinstance(blocks, list) else json.loads(blocks or "[]")

    try:
        compiler = EmailCompiler(blocks_data, preview_text=preview_text or "", email_width=email_width or 600)
        html = compiler.compile()
        return {"html": html}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Letters render_preview error")
        frappe.throw(str(e))




@frappe.whitelist(methods=["POST"])
def duplicate_campaign(name: str):
    """Create an exact copy of a campaign as a new Draft."""
    original = frappe.get_doc("Letters Campaign", name)
    frappe.has_permission("Letters Campaign", "read", doc=original, throw=True)
    frappe.has_permission("Letters Campaign", "create", throw=True)

    new_doc = frappe.get_doc({
        "doctype": "Letters Campaign",
        "title": f"Copy of {original.title}",
        "subject": original.subject or "",
        "preview_text": original.preview_text or "",
        "status": "Draft",
        "email_width": getattr(original, "email_width", None) or 600,
        "blocks_json": original.blocks_json or "[]",
        "recipient_config": getattr(original, "recipient_config", None) or "",
    })
    new_doc.insert()
    # No explicit commit: this is a POST endpoint, so Frappe auto-commits on
    # success. (Manual commits in request handlers are discouraged.)
    return {"name": new_doc.name, "title": new_doc.title}
