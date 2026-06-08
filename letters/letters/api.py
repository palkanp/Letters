import json
import frappe
from frappe import _


@frappe.whitelist()
def get_campaign(name):
    doc = frappe.get_doc("Email Campaign", name)
    return {
        "name": doc.name,
        "title": doc.title,
        "subject": doc.subject,
        "preview_text": doc.preview_text or "",
        "status": doc.status,
        "blocks": json.loads(doc.blocks_json) if doc.blocks_json else [],
    }


@frappe.whitelist()
def save_campaign(name=None, title=None, subject=None, preview_text=None, blocks=None):
    blocks_json = json.dumps(blocks if isinstance(blocks, list) else json.loads(blocks or "[]"))

    if name:
        doc = frappe.get_doc("Email Campaign", name)
        if title is not None:
            doc.title = title
        if subject is not None:
            doc.subject = subject
        if preview_text is not None:
            doc.preview_text = preview_text
        doc.blocks_json = blocks_json
        doc.save()
    else:
        doc = frappe.get_doc({
            "doctype": "Email Campaign",
            "title": title or "Untitled Campaign",
            "subject": subject or "",
            "preview_text": preview_text or "",
            "status": "Draft",
            "blocks_json": blocks_json,
        })
        doc.insert()

    return {"name": doc.name, "title": doc.title}


@frappe.whitelist()
def render_preview(name=None, blocks=None, preview_text=None):
    """Compile blocks to email-safe HTML."""
    from letters.letters.utils.email_compiler import EmailCompiler

    if name and not blocks:
        doc = frappe.get_doc("Email Campaign", name)
        blocks_data = doc.blocks_json or "[]"
        if preview_text is None:
            preview_text = doc.preview_text
    else:
        blocks_data = blocks if isinstance(blocks, list) else json.loads(blocks or "[]")

    try:
        compiler = EmailCompiler(blocks_data, preview_text=preview_text or "")
        html = compiler.compile()
        return {"html": html}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Letters render_preview error")
        frappe.throw(str(e))


def _is_email_field(df):
    """Frappe has no dedicated 'Email' fieldtype on most versions — email fields are
    Data fields with options='Email'. We accept both representations to be safe."""
    return df.fieldtype == "Email" or (df.fieldtype == "Data" and (df.options or "") == "Email")


@frappe.whitelist()
def get_doctypes_with_email_fields():
    """Return doctypes that have at least one email field, that the user can read."""
    doctypes = set()

    # Standard fields (DocField) — match both possible representations.
    for filters in (
        {"fieldtype": "Data", "options": "Email"},
        {"fieldtype": "Email"},
    ):
        for row in frappe.get_all("DocField", filters=filters, fields=["parent"], distinct=True):
            doctypes.add(row.parent)

    # Custom fields live in a separate doctype.
    for filters in (
        {"fieldtype": "Data", "options": "Email"},
        {"fieldtype": "Email"},
    ):
        for row in frappe.get_all("Custom Field", filters=filters, fields=["dt"], distinct=True):
            doctypes.add(row.dt)

    result = []
    for dt in sorted(doctypes):
        try:
            if frappe.has_permission(dt, "read"):
                result.append(dt)
        except Exception:
            pass
    return result


@frappe.whitelist()
def get_email_fields(doctype):
    """Return field names/labels of email fields for a doctype (incl. custom fields)."""
    frappe.has_permission(doctype, "read", throw=True)
    meta = frappe.get_meta(doctype)
    return [
        {"fieldname": df.fieldname, "label": df.label or df.fieldname}
        for df in meta.fields
        if _is_email_field(df)
    ]


@frappe.whitelist()
def get_emails_from_doctype(doctype, email_field, search=None):
    """Return email values from a doctype's email field, with optional name/email search."""
    frappe.has_permission(doctype, "read", throw=True)

    meta = frappe.get_meta(doctype)
    name_field = meta.title_field or "name"

    filters = {email_field: ["!=", ""]}
    if search:
        filters[email_field] = ["like", f"%{search}%"]

    try:
        rows = frappe.get_all(
            doctype,
            filters=filters,
            fields=[name_field, email_field],
            limit=50,
            order_by=f"{name_field} asc",
        )
    except Exception:
        # title_field may not exist as an actual column — fall back to name
        rows = frappe.get_all(
            doctype,
            filters=filters,
            fields=["name", email_field],
            limit=50,
        )
        name_field = "name"

    return [
        {"label": r.get(name_field) or r.get("name"), "email": r.get(email_field)}
        for r in rows
        if r.get(email_field)
    ]


@frappe.whitelist()
def get_email_groups():
    """Return all Email Groups available on the site."""
    groups = frappe.get_all(
        "Email Group",
        fields=["name", "title"],
        order_by="title asc",
    )
    # Attach member count to each group
    for g in groups:
        g["count"] = frappe.db.count(
            "Email Group Member",
            filters={"email_group": g["name"], "unsubscribed": 0},
        )
    return groups


@frappe.whitelist()
def send_campaign(name, recipients=None, email_group=None):
    """
    Compile and send a campaign.

    Pass either:
      - email_group: name of a Frappe Email Group (respects unsubscribes, adds unsubscribe link)
      - recipients:  JSON string or list of email addresses (direct send, no unsubscribe tracking)
    """
    doc = frappe.get_doc("Email Campaign", name)
    if not doc.blocks_json:
        frappe.throw(_("Campaign has no content to send."))
    if not doc.subject:
        frappe.throw(_("Campaign has no subject line."))

    from letters.letters.utils.email_compiler import EmailCompiler
    compiler = EmailCompiler(doc.blocks_json, preview_text=doc.preview_text)
    html = compiler.compile()

    # ── Email Group mode ─────────────────────────────────────────────────────
    if email_group:
        members = frappe.get_all(
            "Email Group Member",
            filters={"email_group": email_group, "unsubscribed": 0},
            fields=["email"],
        )
        recipient_list = [m.email for m in members if m.email]
        if not recipient_list:
            frappe.throw(_("The selected Email Group has no active subscribers."))

        send_doc = frappe.get_doc({
            "doctype": "Email Send",
            "campaign": name,
            "status": "Sending",
            "recipient_emails": "\n".join(recipient_list),
        })
        send_doc.insert(ignore_permissions=True)

        try:
            for email in recipient_list:
                frappe.sendmail(
                    recipients=[email],
                    subject=doc.subject,
                    message=html,
                    now=False,
                    unsubscribe_method="/api/method/frappe.email.doctype.email_group.email_group.unsubscribe",
                    unsubscribe_params={"email_group": email_group},
                )
            send_doc.status = "Sent"
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Letters send_campaign error")
            send_doc.status = "Failed"
            send_doc.save(ignore_permissions=True)
            frappe.throw(_("Failed to queue emails. Check the error log."))

        send_doc.save(ignore_permissions=True)
        doc.status = "Ready"
        doc.save(ignore_permissions=True)
        return {"sent": True, "count": len(recipient_list), "mode": "email_group"}

    # ── Direct recipients mode ────────────────────────────────────────────────
    if isinstance(recipients, str):
        recipients = json.loads(recipients)

    recipients = [r.strip() for r in (recipients or []) if r.strip()]
    if not recipients:
        frappe.throw(_("No recipients provided."))

    send_doc = frappe.get_doc({
        "doctype": "Email Send",
        "campaign": name,
        "status": "Sending",
        "recipient_emails": "\n".join(recipients),
    })
    send_doc.insert(ignore_permissions=True)

    try:
        for email in recipients:
            frappe.sendmail(
                recipients=[email],
                subject=doc.subject,
                message=html,
                now=False,
            )
        send_doc.status = "Sent"
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Letters send_campaign error")
        send_doc.status = "Failed"
        send_doc.save(ignore_permissions=True)
        frappe.throw(_("Failed to queue emails. Check the error log."))

    send_doc.save(ignore_permissions=True)
    doc.status = "Ready"
    doc.save(ignore_permissions=True)
    return {"sent": True, "count": len(recipients), "mode": "direct"}
