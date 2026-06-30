import frappe


def execute():
    if not frappe.db.exists("DocType", "Letter Folder"):
        return
    frappe.rename_doc(
        "DocType",
        "Letter Folder",
        "Letter Category",
        show_alert=False,
    )
    frappe.db.commit()
