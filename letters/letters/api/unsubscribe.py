from __future__ import annotations

import hashlib
import hmac

import frappe
from frappe import _


def _unsub_secret() -> bytes:
    return frappe.utils.cstr(frappe.local.conf.get("secret") or "secret").encode()


def _sign_email(email: str) -> str:
    """HMAC token binding one email address to the preferences page.

    Only ever minted inside unsubscribe_redirect, after Frappe's own
    verify_request() has confirmed the incoming URL carries a valid
    framework signature (see get_unsubcribed_url in frappe/email/queue.py).
    That means a guest can only obtain a token for the address that was the
    genuine recipient of a real unsubscribe link — never an arbitrary one.
    """
    return hmac.new(_unsub_secret(), email.encode(), hashlib.sha256).hexdigest()


@frappe.whitelist(allow_guest=True)
def unsubscribe_redirect(email: str, name: str, **kwargs):
    """Called by Frappe's unsubscribe link for non-email-group sends.

    Redirects to the Letters preferences portal where the recipient can
    opt out of specific categories or all emails.
    """
    from frappe.utils.verified_command import verify_request

    if not (frappe.in_test or verify_request()):
        return

    email = frappe.utils.cstr(email).strip().lower()
    token = _sign_email(email)
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = (
        f"/letters_unsubscribe?email={frappe.utils.cstr(email)}"
        f"&letter={frappe.utils.cstr(name)}&token={token}"
    )


@frappe.whitelist(allow_guest=True)
def save_preferences(email: str, letter: str = "", unsubscribe_folders: str = "", global_unsubscribe: str = "0", token: str = ""):
    """Save unsubscribe preferences submitted from the portal page.

    unsubscribe_folders: comma-separated list of Letter Category names to opt out of.
    Existing category subscriptions NOT in the list are re-activated (deleted from Email Unsubscribe).

    `token` must match the value unsubscribe_redirect minted for this exact
    email — this is what stops a guest from opting an arbitrary address in
    or out without ever having received a genuine unsubscribe link for it.
    """
    email = frappe.utils.cstr(email).strip().lower()
    if not frappe.utils.validate_email_address(email, throw=False):
        frappe.throw(_("Invalid email address."))

    if not token or not hmac.compare_digest(frappe.utils.cstr(token), _sign_email(email)):
        frappe.throw(_("This link is invalid or has expired."), exc=frappe.PermissionError)

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

    # ── Category-level opt-outs ───────────────────────────────────────────────
    selected_folders = {f.strip() for f in unsubscribe_folders.split(",") if f.strip()}
    all_folders      = set(frappe.get_all("Letter Category", pluck="name", ignore_permissions=True))

    for folder in all_folders:
        existing = frappe.db.exists("Email Unsubscribe", {
            "email":             email,
            "reference_doctype": "Letter Category",
            "reference_name":    folder,
        })
        if folder in selected_folders and not existing:
            frappe.get_doc({
                "doctype":           "Email Unsubscribe",
                "email":             email,
                "reference_doctype": "Letter Category",
                "reference_name":    folder,
            }).insert(ignore_permissions=True)
        elif folder not in selected_folders and existing:
            frappe.db.delete("Email Unsubscribe", {
                "email":             email,
                "reference_doctype": "Letter Category",
                "reference_name":    folder,
            })

    frappe.db.commit()
