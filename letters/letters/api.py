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
        doc.title = title or doc.title
        doc.subject = subject or doc.subject
        doc.preview_text = preview_text or doc.preview_text
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
def render_preview(name=None, blocks=None):
    """Compile blocks to email HTML via MJML renderers."""
    from letters.letters.utils.email_compiler import EmailCompiler

    if name and not blocks:
        doc = frappe.get_doc("Email Campaign", name)
        blocks_data = doc.blocks_json or "[]"
    else:
        blocks_data = blocks if isinstance(blocks, list) else json.loads(blocks or "[]")

    try:
        compiler = EmailCompiler(blocks_data)
        html = compiler.compile()
        return {"html": html}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Letters render_preview error")
        frappe.throw(str(e))


@frappe.whitelist()
def send_campaign(name):
    doc = frappe.get_doc("Email Campaign", name)
    if not doc.blocks_json:
        frappe.throw(_("Campaign has no content to send."))

    sends = frappe.get_all(
        "Email Send",
        filters={"campaign": name, "status": "Draft"},
        fields=["name", "recipient_emails"],
    )
    if not sends:
        frappe.throw(_("No draft Email Send records found for this campaign."))

    from letters.letters.utils.email_compiler import EmailCompiler
    compiler = EmailCompiler(doc.blocks_json)
    html = compiler.compile()

    for send_record in sends:
        send_doc = frappe.get_doc("Email Send", send_record["name"])
        recipients = [
            r.strip()
            for r in (send_doc.recipient_emails or "").splitlines()
            if r.strip()
        ]
        if not recipients:
            continue

        send_doc.status = "Sending"
        send_doc.save(ignore_permissions=True)

        for email in recipients:
            frappe.sendmail(
                recipients=[email],
                subject=doc.subject,
                message=html,
                now=False,
            )

        send_doc.status = "Sent"
        send_doc.save(ignore_permissions=True)

    doc.status = "Ready"
    doc.save(ignore_permissions=True)

    return {"sent": True}
