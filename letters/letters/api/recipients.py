from __future__ import annotations

import json

import frappe
from frappe import _




def _load_recipient_config(doc):
    """Parse the letter's saved audience selection.

    Returns a list of source dicts (new multi-source format), a single source
    dict wrapped in a list (old single-source format, normalised on read), or
    None when nothing is stored.
    """
    raw = getattr(doc, "recipient_config", None)
    if not raw:
        return None
    try:
        cfg = json.loads(raw) if isinstance(raw, str) else raw
    except (ValueError, TypeError):
        return None
    if isinstance(cfg, list):
        return cfg if cfg else None
    if isinstance(cfg, dict):
        return [cfg]
    return None




def _normalize_recipient_config(value):
    """Coerce an incoming recipient_config (object, list, or JSON string) to a
    stored JSON string, or "" to clear it. Returns None to mean 'leave unchanged'."""
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    text = str(value).strip()
    if text in ("", "null", "{}"):
        return ""
    return text




def _recipient_args_from_config(doc):
    """Legacy single-source helper — kept for backward compatibility with direct
    send calls that pass explicit email_group/recipients/doctype_config args.

    Returns (recipients, email_group, doctype_config) triple.  For the new
    multi-source array format callers should use _resolve_multi_source instead."""
    sources = _load_recipient_config(doc)
    if not sources:
        return None, None, None
    cfg = sources[0]
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




def _has_recipient_config(doc):
    """Return True when the doc has at least one usable recipient source."""
    sources = _load_recipient_config(doc)
    if not sources:
        return False
    for src in sources:
        t = src.get("type")
        if t == "group" and src.get("email_group"):
            return True
        if t == "paste" and src.get("recipients"):
            return True
        if t == "doctype" and src.get("doctype") and src.get("email_field"):
            return True
    return False




def _resolve_single_source_emails(source):
    """Resolve one source config dict to a raw (unsuppressed) list of emails."""
    stype = source.get("type")
    emails = []

    if stype == "group":
        members = frappe.get_all(
            "Email Group Member",
            filters={"email_group": source.get("email_group", ""), "unsubscribed": 0},
            pluck="email",
        )
        emails = [e for e in members if e]

    elif stype == "paste":
        emails = [e for e in (source.get("recipients") or []) if e]

    elif stype == "doctype":
        dt        = source.get("doctype", "")
        email_fld = source.get("email_field", "")
        filters   = dict(source.get("filters") or {})
        if dt and email_fld:
            frappe.has_permission(dt, "read", throw=True)
            filters[email_fld] = ["!=", ""]
            rows = frappe.get_all(dt, filters=filters, pluck=email_fld, limit=50001)
            emails = [str(r).strip() for r in rows if r]

    return emails




def _resolve_multi_source(sources, max_recipients, suppressed_fn, valid_fn, letter_name=None):
    """Resolve a list of source configs to a final deduplicated, validated
    email list after suppression.  Returns (email_list, invalid_count).

    When letter_name is provided, also snapshots the resolved email list back
    into each source's resolved_emails field on recipient_config so the sent
    view can display per-source recipients exactly.
    """
    seen = set()
    merged = []
    per_source = []  # parallel list of resolved emails per source (pre-dedup within source)

    for src in (sources or []):
        raw = _resolve_single_source_emails(src)
        source_emails = []
        for email in raw:
            e = email.strip().lower()
            if e and e not in seen:
                seen.add(e)
                merged.append(email.strip())
                source_emails.append(email.strip())
        per_source.append(source_emails)

    suppressed = suppressed_fn()
    suppressed_lower = {s.lower() for s in suppressed} if suppressed else set()
    if suppressed_lower:
        merged = [e for e in merged if e.lower() not in suppressed_lower]
        per_source = [
            [e for e in src_emails if e.lower() not in suppressed_lower]
            for src_emails in per_source
        ]

    if not merged:
        frappe.throw(_("No recipients found across all selected audience sources."))

    valid, invalid_count = valid_fn(merged)
    if not valid:
        frappe.throw(_("No valid email addresses to send to."))

    if len(valid) > max_recipients:
        frappe.throw(_(
            "This audience has more than {0} recipients, which is above the "
            "per-letter limit. Narrow your filters or split the send."
        ).format(max_recipients))

    # Snapshot resolved emails back into recipient_config so the sent view
    # can show per-source recipient lists without re-querying.
    if letter_name and sources:
        valid_set = {e.lower() for e in valid}
        updated = []
        for src, src_emails in zip(sources, per_source):
            updated.append({
                **src,
                "resolved_emails": [e for e in src_emails if e.lower() in valid_set],
            })
        frappe.db.set_value(
            "Letter", letter_name, "recipient_config", json.dumps(updated)
        )

    return valid, invalid_count




def _is_email_field(df):
    """Frappe has no dedicated 'Email' fieldtype on most versions; email fields are
    Data fields with options='Email'. We accept both representations to be safe."""
    return df.fieldtype == "Email" or (df.fieldtype == "Data" and (df.options or "") == "Email")




@frappe.whitelist(methods=["GET", "POST"])
def get_doctypes_with_email_fields():
    """Return doctypes that have at least one email field, that the user can read."""
    DocField    = frappe.qb.DocType("DocField")
    CustomField = frappe.qb.DocType("Custom Field")

    df_rows = (
        frappe.qb.from_(DocField)
        .select(DocField.parent)
        .where((DocField.fieldtype == "Email") | ((DocField.fieldtype == "Data") & (DocField.options == "Email")))
        .distinct()
    ).run(as_dict=True)

    cf_rows = (
        frappe.qb.from_(CustomField)
        .select(CustomField.dt)
        .where((CustomField.fieldtype == "Email") | ((CustomField.fieldtype == "Data") & (CustomField.options == "Email")))
        .distinct()
    ).run(as_dict=True)

    doctypes = {r.parent for r in df_rows} | {r.dt for r in cf_rows}

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
    frappe.has_permission("Email Group", "read", throw=True)
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




def _suppressed_emails(letter_name=None):
    """Suppressed emails for a specific letter send.

    Scoped to: global unsubscribes + unsubscribes from this specific letter +
    unsubscribes from the letter's folder. Scoping to the letter name means
    clicking "Unsubscribe" on Letter A will NOT suppress future sends of Letter B.
    """
    or_filters = [{"global_unsubscribe": 1}]
    if letter_name:
        or_filters.append({"reference_doctype": "Letter", "reference_name": letter_name})
        folder = frappe.db.get_value("Letter", letter_name, "folder")
        if folder:
            or_filters.append({"reference_doctype": "Letter Category", "reference_name": folder})
    rows = frappe.get_all(
        "Email Unsubscribe",
        or_filters=or_filters,
        pluck="email",
        distinct=True,
    )
    return {e for e in rows if e}




def _valid_emails(emails):
    """Drop malformed addresses using Frappe's validator (never trust the
    client). Returns (valid_emails, dropped_count)."""
    valid = [e for e in emails if frappe.utils.validate_email_address(e, throw=False)]
    return valid, len(emails) - len(valid)




@frappe.whitelist(methods=["POST"])
def create_email_group_from_source(title: str, source_config: str):
    """Resolve a single source config and save the result as a new Frappe Email Group.

    Returns the new group's name, title, and member count so the frontend can
    convert the source block to a group-type block pointing at the new group.
    """
    source = json.loads(source_config) if isinstance(source_config, str) else source_config
    if not isinstance(source, dict):
        frappe.throw(_("Invalid source configuration."))

    emails_raw = _resolve_single_source_emails(source)
    valid, _ = _valid_emails(emails_raw)
    if not valid:
        frappe.throw(_("No valid email addresses found in this source."))

    group = frappe.get_doc({"doctype": "Email Group", "title": title})
    group.insert()

    now  = frappe.utils.now()
    user = frappe.session.user
    fields = [
        "name", "creation", "modified", "modified_by", "owner", "docstatus",
        "idx", "email_group", "email", "unsubscribed",
    ]
    values = [
        (
            frappe.generate_hash(length=10), now, now, user, user, 0,
            idx + 1, group.name, email, 0,
        )
        for idx, email in enumerate(valid)
    ]
    frappe.db.bulk_insert("Email Group Member", fields=fields, values=values)
    frappe.db.commit()

    return {"name": group.name, "title": group.title, "count": len(valid)}
