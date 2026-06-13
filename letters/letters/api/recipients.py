from __future__ import annotations

import json

import frappe
from frappe import _




def _load_recipient_config(doc):
    """Parse the campaign's saved audience selection into a dict (or None)."""
    raw = getattr(doc, "recipient_config", None)
    if not raw:
        return None
    try:
        cfg = json.loads(raw) if isinstance(raw, str) else raw
    except (ValueError, TypeError):
        return None
    return cfg if isinstance(cfg, dict) else None




def _normalize_recipient_config(value):
    """Coerce an incoming recipient_config (object or JSON string) to a stored
    JSON string, or "" to clear it. Returns None to mean 'leave unchanged'."""
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    text = str(value).strip()
    if text in ("", "null", "{}"):
        return ""
    return text




def _recipient_args_from_config(doc):
    """Translate the campaign's saved recipient_config into the (recipients,
    email_group, doctype_config) triple that send_campaign resolves. Returns
    (None, None, None) when nothing usable is stored."""
    cfg = _load_recipient_config(doc)
    if not cfg:
        return None, None, None
    ctype = cfg.get("type")
    if ctype == "group" and cfg.get("email_group"):
        return None, cfg["email_group"], None
    if ctype == "paste" and cfg.get("recipients"):
        return cfg["recipients"], None, None
    if ctype == "doctype" and cfg.get("doctype") and cfg.get("email_field"):
        return None, None, {
            "doctype":     cfg["doctype"],
            "email_field": cfg["email_field"],
            "filters":     cfg.get("filters") or {},
        }
    return None, None, None




def _is_email_field(df):
    """Frappe has no dedicated 'Email' fieldtype on most versions; email fields are
    Data fields with options='Email'. We accept both representations to be safe."""
    return df.fieldtype == "Email" or (df.fieldtype == "Data" and (df.options or "") == "Email")




@frappe.whitelist(methods=["GET", "POST"])
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




@frappe.whitelist(methods=["GET", "POST"])
def get_email_fields(doctype: str):
    """Return field names/labels of email fields for a doctype (incl. custom fields)."""
    frappe.has_permission(doctype, "read", throw=True)
    meta = frappe.get_meta(doctype)
    return [
        {"fieldname": df.fieldname, "label": df.label or df.fieldname}
        for df in meta.fields
        if _is_email_field(df)
    ]




@frappe.whitelist(methods=["GET", "POST"])
def get_doctype_filter_fields(doctype: str):
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




@frappe.whitelist(methods=["GET", "POST"])
def count_doctype_recipients(doctype: str, email_field: str, filters: str | None = None):
    """Preview how many records match the given filter config."""
    frappe.has_permission(doctype, "read", throw=True)
    filter_dict = json.loads(filters) if isinstance(filters, str) else (filters or {})
    filter_dict[email_field] = ["!=", ""]
    try:
        count = frappe.db.count(doctype, filter_dict)
    except Exception:
        count = 0
    return {"count": count}




@frappe.whitelist(methods=["GET", "POST"])
def get_email_groups():
    """Return all Email Groups with active member counts (single GROUP BY query)."""
    groups = frappe.get_all(
        "Email Group",
        fields=["name", "title"],
        order_by="title asc",
    )
    if not groups:
        return groups

    # Single GROUP BY query via the query builder. (Raw SQL functions passed as
    # field strings — e.g. "count(*) as cnt" — are rejected by recent Frappe for
    # SQL-injection safety, so we build the aggregate with frappe.qb instead.)
    from frappe.query_builder.functions import Count

    EGM = frappe.qb.DocType("Email Group Member")
    count_rows = (
        frappe.qb.from_(EGM)
        .select(EGM.email_group, Count(EGM.name).as_("cnt"))
        .where(EGM.unsubscribed == 0)
        .groupby(EGM.email_group)
    ).run(as_dict=True)
    counts = {r["email_group"]: r["cnt"] for r in count_rows}

    for g in groups:
        g["count"] = counts.get(g["name"], 0)
    return groups




def _suppressed_emails():
    """Addresses that have unsubscribed from Letters (any campaign) or globally.

    Reuses Frappe's native Email Unsubscribe store, which is populated by the
    signed unsubscribe footer Frappe injects into every campaign email (see the
    reference_doctype/reference_name passed in _execute_send). Filtering here
    makes an unsubscribe apply across *all* Letters campaigns, not just resends
    of the one the recipient clicked from."""
    rows = frappe.get_all(
        "Email Unsubscribe",
        or_filters=[
            {"reference_doctype": "Letters Campaign"},
            {"global_unsubscribe": 1},
        ],
        pluck="email",
        distinct=True,
    )
    return {e for e in rows if e}




def _valid_emails(emails):
    """Drop malformed addresses using Frappe's validator (never trust the
    client). Returns (valid_emails, dropped_count)."""
    valid = [e for e in emails if frappe.utils.validate_email_address(e, throw=False)]
    return valid, len(emails) - len(valid)
