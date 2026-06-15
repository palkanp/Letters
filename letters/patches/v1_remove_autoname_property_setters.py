"""
Remove the three Property Setters that were added via the Frappe UI to configure
Letter autoname. These settings now live in the doctype JSON directly,
so the Property Setters are redundant and cause a title-revert bug on save.
"""
import frappe


def execute():
    stale = [
        "Letter-main-autoname",
        "Letter-main-naming_rule",
        "Letter-title-unique",
    ]
    for name in stale:
        if frappe.db.exists("Property Setter", name):
            frappe.db.delete("Property Setter", {"name": name})
    frappe.clear_cache(doctype="Letter")
