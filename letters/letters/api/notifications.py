from __future__ import annotations

import frappe


@frappe.whitelist()
def get_all_notifications():
    """Return all Notifications that have a Letter linked."""
    frappe.has_permission("Notification", "read", throw=True)
    return frappe.get_all(
        "Notification",
        filters={"letter": ("is", "set")},
        fields=["name", "subject", "document_type", "event", "enabled", "letter", "modified"],
        order_by="modified desc",
        limit=200,
    )


@frappe.whitelist()
def get_notification_for_letter(letter: str):
    """Return the single Notification linked to this Letter, or None."""
    frappe.has_permission("Notification", "read", throw=True)
    name = frappe.db.get_value("Notification", {"letter": letter}, "name")
    if not name:
        return None
    return frappe.db.get_value(
        "Notification",
        name,
        ["name", "subject", "document_type", "event", "enabled"],
        as_dict=True,
    )


@frappe.whitelist()
def create_notification_for_letter(letter: str):
    """Create a new disabled Notification linked to this Letter and return its name."""
    frappe.has_permission("Letter", "read", throw=True)
    frappe.has_permission("Notification", "create", throw=True)

    existing = frappe.db.get_value("Notification", {"letter": letter}, "name")
    if existing:
        return {"name": existing}

    letter_doc = frappe.get_doc("Letter", letter)
    if letter_doc.status in ("Sent", "Partial", "Failed", "Sending", "Scheduled"):
        frappe.throw("A sent or scheduled letter cannot be converted to a Notification.")

    base_name = f"Letters – {letter_doc.title}"
    notif_name = base_name
    if frappe.db.exists("Notification", notif_name):
        notif_name = f"{base_name} ({frappe.generate_hash(length=4)})"

    notification = frappe.get_doc({
        "doctype": "Notification",
        "name": notif_name,
        "subject": letter_doc.subject or "",
        "document_type": "User",
        "event": "New",
        "channel": "Email",
        "message": "",
        "enabled": 0,
        "letter": letter,
    })
    notification.flags.ignore_mandatory = True
    notification.insert(ignore_permissions=True)
    frappe.db.commit()

    return {"name": notification.name}


@frappe.whitelist()
def create_notification_pair():
    """Create a blank Letter and a linked Notification together, return both names."""
    frappe.has_permission("Letter", "create", throw=True)

    from letters.letters.doctype.letter._content import _unique_letter_title

    letter = frappe.get_doc({
        "doctype": "Letter",
        "title": _unique_letter_title("Notification Email"),
        "subject": "",
        "status": "Draft",
        "email_width": 600,
        "canvas_background": "#ffffff",
        "blocks_json": "[]",
    })
    letter.insert(ignore_permissions=True)

    base_name = f"Letters – {letter.title}"
    notif_name = base_name
    if frappe.db.exists("Notification", notif_name):
        notif_name = f"{base_name} ({frappe.generate_hash(length=4)})"

    notification = frappe.get_doc({
        "doctype": "Notification",
        "name": notif_name,
        "subject": "",
        "document_type": "User",
        "event": "New",
        "channel": "Email",
        "message": "",
        "enabled": 0,
        "letter": letter.name,
    })
    notification.flags.ignore_mandatory = True
    notification.insert(ignore_permissions=True)
    frappe.db.commit()

    return {"letter": letter.name, "notification": notif_name}


@frappe.whitelist()
def duplicate_notification_pair(name: str):
    """Duplicate a Notification and its linked Letter together."""
    notif = frappe.get_doc("Notification", name)
    frappe.has_permission("Notification", "create", doc=notif, throw=True)
    if not notif.get("letter"):
        frappe.throw("This notification has no linked letter.")

    letter_doc = frappe.get_doc("Letter", notif.letter)
    dup_letter = letter_doc.duplicate()

    new_notif = frappe.copy_doc(notif)
    base_name = f"Copy of {name}"
    new_notif.name = base_name if not frappe.db.exists("Notification", base_name) else f"{base_name} ({frappe.generate_hash(length=4)})"
    new_notif.letter = dup_letter["name"]
    new_notif.enabled = 0
    new_notif.flags.ignore_mandatory = True
    new_notif.insert(ignore_permissions=True)
    frappe.db.commit()

    return {"letter": dup_letter["name"], "notification": new_notif.name}


@frappe.whitelist()
def delete_notification_pair(name: str):
    """Delete a Notification and its linked Letter together."""
    notif = frappe.get_doc("Notification", name)
    frappe.has_permission("Notification", "delete", doc=notif, throw=True)
    letter_name = notif.get("letter")
    frappe.delete_doc("Notification", name, ignore_permissions=True)
    if letter_name:
        frappe.delete_doc("Letter", letter_name, ignore_permissions=True)
    frappe.db.commit()


@frappe.whitelist()
def get_notification_detail(notification: str):
    """Return full Notification doc (with recipients child table) for inline editing."""
    frappe.has_permission("Notification", "read", throw=True)
    doc = frappe.get_doc("Notification", notification)
    result = doc.as_dict()
    # Trim recipients to only the fields the UI needs (as_dict already has them)
    result["recipients"] = [
        {
            "name": r.get("name") or "",
            "receiver_by_document_field": r.get("receiver_by_document_field") or "",
            "receiver_by_role": r.get("receiver_by_role") or "",
            "cc": r.get("cc") or "",
            "bcc": r.get("bcc") or "",
            "condition": r.get("condition") or "",
        }
        for r in result.get("recipients", [])
    ]
    return result


@frappe.whitelist()
def save_notification_fields(notification: str, fields: str):
    """Patch allowed fields on a Notification doc, skipping mandatory validation."""
    import json
    frappe.has_permission("Notification", "write", throw=True)
    data = json.loads(fields)
    doc = frappe.get_doc("Notification", notification)

    SCALAR_FIELDS = {
        "enabled", "document_type", "event", "condition_type", "condition",
        "filters", "sender", "sender_email", "date_changed", "days_in_advance",
        "value_changed", "method",
    }
    for key, val in data.items():
        if key in SCALAR_FIELDS:
            setattr(doc, key, val)

    if "recipients" in data:
        rows = []
        for r in data["recipients"]:
            row = {
                "doctype": "Notification Recipient",
                "receiver_by_document_field": r.get("receiver_by_document_field") or "",
                "receiver_by_role": r.get("receiver_by_role") or "",
                "cc": r.get("cc") or "",
                "bcc": r.get("bcc") or "",
                "condition": r.get("condition") or "",
            }
            if r.get("name"):
                row["name"] = r["name"]
            rows.append(row)
        doc.set("recipients", rows)

    doc.flags.ignore_mandatory = True
    doc.save(ignore_permissions=True)
    return {"ok": True}


@frappe.whitelist()
def get_merge_fields(letter: str):
    """Return the Jinja merge fields available for this Letter's linked Notification.

    Sourced from the Notification's `document_type` — the same doctype whose
    fields resolve at send time via `{{ doc.<fieldname> }}` (see
    LettersNotification.send_an_email -> frappe.render_template). Returns None
    if the Letter has no linked Notification, or one with no document_type set
    yet, so the caller can show "pick a Document Type first" instead.
    """
    frappe.has_permission("Notification", "read", throw=True)
    document_type = frappe.db.get_value("Notification", {"letter": letter}, "document_type")
    if not document_type:
        return None

    meta = frappe.get_meta(document_type)
    fields = [{"label": "Name (ID)", "fieldname": "name"}]
    for df in meta.fields:
        if df.fieldtype in (
            "Data", "Link", "Select", "Int", "Float", "Currency", "Date",
            "Datetime", "Check", "Small Text", "Text", "Long Text",
        ):
            fields.append({"label": df.label or df.fieldname, "fieldname": df.fieldname})

    return {"document_type": document_type, "fields": fields}


def resolve_merge_tags_for_preview(html: str, letter_name: str | None) -> str:
    """Resolve `{{ doc.field }}` tags in a compiled Letter preview, if it has a
    linked, configured Notification.

    Mirrors LettersNotification.send_an_email: real sends run the compiled
    Letter HTML through `frappe.render_template` against the triggering
    document. There's no live document at preview time, so this substitutes
    the most recently modified record of the Notification's `document_type`
    as a stand-in. Returns `html` unchanged if there's no linked Notification,
    no `document_type` set yet, or no sample record to render against.
    """
    if not letter_name:
        return html
    notif_name = frappe.db.get_value("Notification", {"letter": letter_name}, "name")
    if not notif_name:
        return html
    document_type = frappe.db.get_value("Notification", notif_name, "document_type")
    if not document_type:
        return html
    sample_name = frappe.db.get_value(document_type, {}, "name", order_by="modified desc")
    if not sample_name:
        return html

    from frappe.email.doctype.notification.notification import get_context

    notif = frappe.get_doc("Notification", notif_name)
    doc = frappe.get_cached_doc(document_type, sample_name)
    context = get_context(doc)
    context.update({"alert": notif, "comments": None})
    try:
        return frappe.render_template(html, context)
    except Exception:
        return html


@frappe.whitelist()
def create_letter_for_notification(notification: str):
    """Create a blank Letter, link it to an existing Notification, and return the letter name."""
    frappe.has_permission("Notification", "write", throw=True)

    notif_doc = frappe.get_doc("Notification", notification)

    if notif_doc.get("letter"):
        return {"letter": notif_doc.letter}

    from letters.letters.doctype.letter._content import _unique_letter_title

    letter = frappe.get_doc({
        "doctype": "Letter",
        "title": _unique_letter_title(f"Notification: {notif_doc.name}"),
        "subject": notif_doc.subject or "",
        "status": "Draft",
        "email_width": 600,
        "canvas_background": "#ffffff",
        "blocks_json": "[]",
    })
    letter.insert(ignore_permissions=True)

    frappe.db.set_value("Notification", notification, "letter", letter.name)
    frappe.db.commit()

    return {"letter": letter.name}
