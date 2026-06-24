import frappe
from frappe import _

no_cache = 1


def get_context(context):
    email  = frappe.utils.cstr(frappe.request.args.get("email", "")).strip().lower()
    letter = frappe.utils.cstr(frappe.request.args.get("letter", "")).strip()
    saved  = frappe.utils.cint(frappe.request.args.get("saved", 0))

    context.email  = email
    context.letter = letter
    context.saved  = saved
    context.title  = _("Email Preferences")
    context.no_sidebar = 1

    if not email:
        context.folders           = []
        context.is_globally_unsubscribed = False
        return

    # All Letter Folders
    folders = frappe.get_all("Letter Folder", fields=["name", "folder_name"], order_by="folder_name asc")
    for f in folders:
        f["is_unsubscribed"] = bool(frappe.db.exists("Email Unsubscribe", {
            "email":             email,
            "reference_doctype": "Letter Folder",
            "reference_name":    f["name"],
        }))

    context.folders = folders
    context.is_globally_unsubscribed = bool(frappe.db.exists("Email Unsubscribe", {
        "email":             email,
        "global_unsubscribe": 1,
    }))
