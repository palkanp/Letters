from __future__ import annotations

import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def unsubscribe_redirect(email: str, name: str, **kwargs):
    """Called by Frappe's unsubscribe link for non-email-group sends.

    Redirects to the Letters preferences portal where the recipient can
    opt out of specific folders or all Frappe emails.
    """
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = (
        f"/letters-unsubscribe?email={frappe.utils.cstr(email)}&letter={frappe.utils.cstr(name)}"
    )


@frappe.whitelist(allow_guest=True)
def save_preferences(email: str, letter: str = "", unsubscribe_folders: str = "", global_unsubscribe: str = "0"):
    """Save unsubscribe preferences submitted from the portal page.

    unsubscribe_folders: comma-separated list of Letter Folder names to opt out of.
    Existing folder subscriptions NOT in the list are re-activated (deleted from Email Unsubscribe).
    """
    email = frappe.utils.cstr(email).strip().lower()
    if not frappe.utils.validate_email_address(email, throw=False):
        frappe.throw(_("Invalid email address."))

    # ── Global unsubscribe ────────────────────────────────────────────────────
    do_global = frappe.utils.cint(global_unsubscribe) == 1
    existing_global = frappe.db.exists("Email Unsubscribe", {"email": email, "global_unsubscribe": 1})
    if do_global and not existing_global:
        frappe.get_doc({
            "doctype": "Email Unsubscribe",
            "email":             email,
            "global_unsubscribe": 1,
        }).insert(ignore_permissions=True)
    elif not do_global and existing_global:
        frappe.db.delete("Email Unsubscribe", {"email": email, "global_unsubscribe": 1})

    # ── Folder-level opt-outs ─────────────────────────────────────────────────
    selected_folders = {f.strip() for f in unsubscribe_folders.split(",") if f.strip()}
    all_folders      = {r.name for r in frappe.get_all("Letter Folder", pluck="name")}

    for folder in all_folders:
        existing = frappe.db.exists("Email Unsubscribe", {
            "email":             email,
            "reference_doctype": "Letter Folder",
            "reference_name":    folder,
        })
        if folder in selected_folders and not existing:
            frappe.get_doc({
                "doctype":           "Email Unsubscribe",
                "email":             email,
                "reference_doctype": "Letter Folder",
                "reference_name":    folder,
            }).insert(ignore_permissions=True)
        elif folder not in selected_folders and existing:
            frappe.db.delete("Email Unsubscribe", {
                "email":             email,
                "reference_doctype": "Letter Folder",
                "reference_name":    folder,
            })

    frappe.db.commit()
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = "/letters-unsubscribe?saved=1"
