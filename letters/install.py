import frappe


def after_install():
    seed_templates()
    _add_notification_letter_field()
    _add_notification_message_type_field()


def after_migrate():
    seed_templates()
    _add_notification_letter_field()
    _add_notification_message_type_field()


def seed_templates():
    import json
    import os

    fixture_path = os.path.join(
        frappe.get_app_path('letters'), 
        "letters", "fixtures", 
        "letters_template.json"
    )
    with open(fixture_path) as f:
        templates = json.load(f)

    for tpl in templates:
        name = tpl.get("name")
        if frappe.db.exists("Letters Template", name):
            doc = frappe.get_doc("Letters Template", name)
            doc.update(tpl)
            doc.save(ignore_permissions=True)
        else:
            doc = frappe.get_doc({"doctype": "Letters Template", **tpl})
            doc.insert(ignore_permissions=True)

    frappe.db.commit()


def _add_notification_message_type_field():
    """Add/update the letter_message_type Select field on Notification (idempotent)."""
    desired = {
        "dt": "Notification",
        "fieldname": "letter_message_type",
        "fieldtype": "Select",
        "options": "Custom Message\nLetter Builder",
        "label": "Email Body",
        "default": "Custom Message",
        "insert_after": "message_sb",
        "translatable": 0,
    }
    if frappe.db.exists("Custom Field", "Notification-letter_message_type"):
        frappe.db.set_value("Custom Field", "Notification-letter_message_type", "insert_after", "message_sb")
    else:
        frappe.get_doc({"doctype": "Custom Field", **desired}).insert(ignore_permissions=True)
    frappe.db.commit()


def _add_notification_letter_field():
    """Add a Letter link field to Frappe's Notification DocType (idempotent)."""
    if frappe.db.exists("Custom Field", "Notification-letter"):
        return
    frappe.get_doc({
        "doctype": "Custom Field",
        "dt": "Notification",
        "fieldname": "letter",
        "fieldtype": "Link",
        "options": "Letter",
        "label": "Letter",
        "description": "Use a visual Letter design as the email body for this notification",
        "insert_after": "message",
        "translatable": 0,
    }).insert(ignore_permissions=True)
    frappe.db.commit()
