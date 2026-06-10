import json
import frappe
from frappe import _

# Hard ceiling on a single campaign's audience. Above this we refuse the send
# with a clear message rather than silently dropping recipients. Tune as needed
# for your sending infrastructure.
MAX_RECIPIENTS = 50000


@frappe.whitelist()
def get_campaign(name):
    doc = frappe.get_doc("Letters Campaign", name)
    frappe.has_permission("Letters Campaign", "read", doc=doc, throw=True)
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
        doc = frappe.get_doc("Letters Campaign", name)
        frappe.has_permission("Letters Campaign", "write", doc=doc, throw=True)
        if title is not None:
            doc.title = title
        if subject is not None:
            doc.subject = subject
        if preview_text is not None:
            doc.preview_text = preview_text
        doc.blocks_json = blocks_json
        doc.save()
    else:
        frappe.has_permission("Letters Campaign", "create", throw=True)
        doc = frappe.get_doc({
            "doctype": "Letters Campaign",
            "title": title or "Untitled Campaign",
            "subject": subject or "",
            "preview_text": preview_text or "",
            "status": "Draft",
            "blocks_json": blocks_json,
        })
        doc.insert()

    return {"name": doc.name, "title": doc.title, "status": doc.status}


@frappe.whitelist()
def render_preview(name=None, blocks=None, preview_text=None):
    """Compile blocks to email-safe HTML."""
    from letters.letters.utils.email_compiler import EmailCompiler

    if name and not blocks:
        doc = frappe.get_doc("Letters Campaign", name)
        frappe.has_permission("Letters Campaign", "read", doc=doc, throw=True)
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
def duplicate_campaign(name):
    """Create an exact copy of a campaign as a new Draft."""
    original = frappe.get_doc("Letters Campaign", name)
    frappe.has_permission("Letters Campaign", "read", doc=original, throw=True)
    frappe.has_permission("Letters Campaign", "create", throw=True)

    new_doc = frappe.get_doc({
        "doctype": "Letters Campaign",
        "title": f"Copy of {original.title}",
        "subject": original.subject or "",
        "preview_text": original.preview_text or "",
        "status": "Draft",
        "blocks_json": original.blocks_json or "[]",
    })
    new_doc.insert()
    frappe.db.commit()
    return {"name": new_doc.name, "title": new_doc.title}


@frappe.whitelist()
def send_test(blocks=None, subject=None, preview_text=None, name=None):
    """Send a test email to the currently logged-in user."""
    from letters.letters.utils.email_compiler import EmailCompiler

    if name and not blocks:
        doc = frappe.get_doc("Letters Campaign", name)
        frappe.has_permission("Letters Campaign", "read", doc=doc, throw=True)
        blocks_data = doc.blocks_json or "[]"
        subject = subject or doc.subject
        preview_text = preview_text or doc.preview_text
    else:
        blocks_data = blocks if isinstance(blocks, list) else json.loads(blocks or "[]")

    try:
        compiler = EmailCompiler(blocks_data, preview_text=preview_text or "")
        html = compiler.compile()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Letters send_test compile error")
        frappe.throw(str(e))

    email = frappe.session.user
    test_subject = f"[TEST] {subject or 'Email Preview'}"

    frappe.sendmail(
        recipients=[email],
        subject=test_subject,
        message=html,
        now=True,
    )
    return {"sent_to": email}


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

    emails = [
        {"label": r.get(name_field) or r.get("name"), "email": r.get(email_field)}
        for r in rows
        if r.get(email_field)
    ]
    return {"emails": emails, "truncated": len(rows) >= 50}


@frappe.whitelist()
def get_doctype_filter_fields(doctype):
    """Return fields suitable as filters for the given doctype.

    Returns Select, Link, and Date/Datetime fields so the user can
    narrow recipients by criteria like Status, Territory, or creation date.
    Also always includes "creation" and "modified" system fields.
    """
    frappe.has_permission(doctype, "read", throw=True)
    meta = frappe.get_meta(doctype)

    FILTER_TYPES = {"Select", "Link", "Date", "Datetime"}
    fields = []
    seen = set()

    for df in meta.fields:
        if df.fieldtype not in FILTER_TYPES:
            continue
        if df.fieldname in seen:
            continue
        seen.add(df.fieldname)
        entry = {
            "fieldname": df.fieldname,
            "label": df.label or df.fieldname,
            "fieldtype": df.fieldtype,
        }
        if df.fieldtype == "Select" and df.options:
            entry["options"] = [o for o in df.options.split("\n") if o.strip()]
        elif df.fieldtype == "Link":
            entry["options_doctype"] = df.options or ""
        fields.append(entry)

    # Always offer creation date filter
    for sys_field in ("creation", "modified"):
        if sys_field not in seen:
            fields.append({
                "fieldname": sys_field,
                "label": sys_field.capitalize(),
                "fieldtype": "Datetime",
            })

    return fields


@frappe.whitelist()
def count_doctype_recipients(doctype, email_field, filters=None):
    """Preview how many records match the given filter config."""
    frappe.has_permission(doctype, "read", throw=True)
    filter_dict = json.loads(filters) if isinstance(filters, str) else (filters or {})
    filter_dict[email_field] = ["!=", ""]
    try:
        count = frappe.db.count(doctype, filter_dict)
    except Exception:
        count = 0
    return {"count": count}


@frappe.whitelist()
def get_email_groups():
    """Return all Email Groups with active member counts (single GROUP BY query)."""
    groups = frappe.get_all(
        "Email Group",
        fields=["name", "title"],
        order_by="title asc",
    )
    if not groups:
        return groups

    # Single aggregation query instead of N separate frappe.db.count() calls
    count_rows = frappe.db.get_all(
        "Email Group Member",
        filters={"unsubscribed": 0},
        fields=["email_group", "count(*) as cnt"],
        group_by="email_group",
    )
    counts = {r["email_group"]: r["cnt"] for r in count_rows}

    for g in groups:
        g["count"] = counts.get(g["name"], 0)
    return groups


@frappe.whitelist()
def send_campaign(name, recipients=None, email_group=None, doctype_config=None):
    """
    Compile and send a campaign.

    Pass one of:
      - email_group:    name of a Frappe Email Group (respects unsubscribes)
      - recipients:     JSON string or list of email addresses
      - doctype_config: JSON string/dict with keys:
                          doctype, email_field, filters (dict of frappe filter expressions)

    The actual per-recipient loop is enqueued as a background job so large lists
    do not block the web request or risk a gunicorn timeout.
    """
    doc = frappe.get_doc("Letters Campaign", name)
    frappe.has_permission("Letters Campaign", "write", doc=doc, throw=True)

    # Idempotency guard — prevent duplicate sends (check both status and DB)
    if doc.status in ("Sent", "Sending"):
        frappe.throw(_("This campaign has already been sent or is currently sending."))
    already_sent = frappe.db.exists(
        "Email Send", {"campaign": name, "status": ["in", ["Sent", "Sending"]]}
    )
    if already_sent:
        frappe.throw(_("This campaign has already been sent. Duplicate sends are not allowed."))

    if not doc.blocks_json:
        frappe.throw(_("Campaign has no content to send."))
    if not doc.subject:
        frappe.throw(_("Campaign has no subject line."))

    # ── Resolve recipient list synchronously so we can fail fast ─────────────
    if email_group:
        members = frappe.get_all(
            "Email Group Member",
            filters={"email_group": email_group, "unsubscribed": 0},
            fields=["email"],
        )
        recipient_list = [m.email for m in members if m.email]
        if not recipient_list:
            frappe.throw(_("The selected Email Group has no active subscribers."))
        mode = "email_group"
    elif doctype_config:
        cfg = json.loads(doctype_config) if isinstance(doctype_config, str) else doctype_config
        dt         = cfg.get("doctype")
        email_fld  = cfg.get("email_field")
        filters    = cfg.get("filters") or {}
        if not dt or not email_fld:
            frappe.throw(_("doctype_config must include doctype and email_field."))
        frappe.has_permission(dt, "read", throw=True)
        filters[email_fld] = ["!=", ""]
        # Fetch one past the cap so we can detect (and reject) an oversized
        # audience instead of silently truncating it.
        rows = frappe.get_all(dt, filters=filters, fields=[email_fld], limit=MAX_RECIPIENTS + 1)
        recipient_list = [r.get(email_fld, "").strip() for r in rows if r.get(email_fld, "").strip()]
        if not recipient_list:
            frappe.throw(_("No records match the selected filters."))
        email_group = None
        mode = "direct"
    else:
        if isinstance(recipients, str):
            recipients = json.loads(recipients)
        recipient_list = [r.strip() for r in (recipients or []) if r.strip()]
        if not recipient_list:
            frappe.throw(_("No recipients provided."))
        email_group = None
        mode = "direct"

    # ── Guard against an oversized audience (no silent truncation) ───────────
    if len(recipient_list) > MAX_RECIPIENTS:
        frappe.throw(_(
            "This audience has more than {0} recipients, which is above the "
            "per-campaign limit. Narrow your filters or split the send."
        ).format(MAX_RECIPIENTS))

    # ── Claim the send synchronously to prevent a race between two requests ──
    send_doc = frappe.get_doc({
        "doctype": "Email Send",
        "campaign": name,
        "status": "Sending",
        "recipient_emails": "\n".join(recipient_list),
    })
    send_doc.insert(ignore_permissions=True)
    frappe.db.commit()  # flush so the background job can read the send_doc

    # Mark campaign as Sending before returning so any re-submit attempt is blocked
    doc.status = "Sending"
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    # ── Enqueue the actual per-recipient loop as a background job ─────────────
    frappe.enqueue(
        "letters.letters.api._execute_send",
        queue="long",
        timeout=600,
        job_name=f"letters_send_{name}",
        send_doc_name=send_doc.name,
        campaign_name=name,
        recipient_list=recipient_list,
        email_group=email_group,
        mode=mode,
    )

    return {"queued": True, "count": len(recipient_list), "mode": mode}


def _execute_send(send_doc_name, campaign_name, recipient_list, email_group, mode):
    """
    Background job: compile the campaign and send one email per recipient.
    Runs in a worker process — must NOT be decorated with @frappe.whitelist().
    """
    try:
        doc = frappe.get_doc("Letters Campaign", campaign_name)
        send_doc = frappe.get_doc("Email Send", send_doc_name)

        from letters.letters.utils.email_compiler import EmailCompiler
        compiler = EmailCompiler(doc.blocks_json, preview_text=doc.preview_text)
        html = compiler.compile()

        for email in recipient_list:
            kwargs = dict(
                recipients=[email],
                subject=doc.subject,
                message=html,
                now=False,
            )
            if mode == "email_group" and email_group:
                kwargs["unsubscribe_method"] = (
                    "/api/method/frappe.email.doctype.email_group"
                    ".email_group.unsubscribe"
                )
                kwargs["unsubscribe_params"] = {"email_group": email_group}
            frappe.sendmail(**kwargs)

        send_doc.status = "Sent"
        send_doc.save(ignore_permissions=True)
        doc.status = "Sent"
        doc.save(ignore_permissions=True)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Letters _execute_send error")
        try:
            send_doc = frappe.get_doc("Email Send", send_doc_name)
            send_doc.status = "Failed"
            send_doc.save(ignore_permissions=True)
            campaign_doc = frappe.get_doc("Letters Campaign", campaign_name)
            campaign_doc.status = "Draft"  # allow re-send after failure
            campaign_doc.save(ignore_permissions=True)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Letters _execute_send cleanup error")
