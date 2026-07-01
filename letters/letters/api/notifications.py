from __future__ import annotations

import frappe


@frappe.whitelist()
def get_all_notifications():
    """Return all Notifications that have a Letter linked."""
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
