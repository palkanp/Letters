"""
Remove the three Property Setters that were added via the Frappe UI to configure
Letters Campaign autoname. These settings now live in the doctype JSON directly,
so the Property Setters are redundant and cause a title-revert bug on save.
"""
import frappe


def execute():
    stale = [
        "Letters Campaign-main-autoname",
        "Letters Campaign-main-naming_rule",
        "Letters Campaign-title-unique",
    ]
    for name in stale:
        if frappe.db.exists("Property Setter", name):
            frappe.db.delete("Property Setter", {"name": name})
    frappe.clear_cache(doctype="Letters Campaign")
