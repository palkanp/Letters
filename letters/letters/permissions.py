import frappe

LETTER_BUILDER_PAGE = "letter-builder"
GATED_DOCTYPE = "Letter"


def sync_letter_builder_page_roles(doc=None, method=None):
    """Keep the Letter Builder page's roles in sync with read access on Letter.

    Runs on Custom DocPerm changes (Role Permission Manager) and after migrate,
    so granting a role read access on Letter automatically opens the builder to it.
    """
    if doc is not None and doc.parent != GATED_DOCTYPE:
        return

    custom_docperm_filters = {"parent": GATED_DOCTYPE, "permlevel": 0, "read": 1}
    if doc is not None and method == "on_trash":
        # on_trash fires before the row is actually removed from the DB.
        custom_docperm_filters["name"] = ["!=", doc.name]

    permitted_roles = set(
        frappe.get_all(
            "DocPerm",
            filters={"parent": GATED_DOCTYPE, "permlevel": 0, "read": 1},
            pluck="role",
        )
    )
    permitted_roles.update(
        frappe.get_all(
            "Custom DocPerm",
            filters=custom_docperm_filters,
            pluck="role",
        )
    )
    permitted_roles.discard(None)
    if not permitted_roles:
        # Never let the page's roles table go empty - that would open it to everyone.
        return

    page = frappe.get_doc("Page", LETTER_BUILDER_PAGE)
    existing_roles = {row.role for row in page.roles}
    if permitted_roles == existing_roles:
        return

    page.roles = []
    for role in sorted(permitted_roles):
        page.append("roles", {"role": role})
    page.flags.ignore_permissions = True
    page.flags.ignore_mandatory = True
    page.save()
    frappe.clear_cache(doctype="Page")
