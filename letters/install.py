import frappe


def after_install():
    seed_templates()


def after_migrate():
    seed_templates()


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
