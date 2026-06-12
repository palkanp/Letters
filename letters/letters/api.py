import json
import frappe
from frappe import _

# Hard ceiling on a single campaign's audience. Above this we refuse the send
# with a clear message rather than silently dropping recipients. Tune as needed
# for your sending infrastructure.
MAX_RECIPIENTS = 50000

# Background send-job timeout in seconds.
SEND_JOB_TIMEOUT = 600

# Flush per-recipient progress to the DB every N sends so a worker crash mid-batch
# loses at most this many recipients' tracked status (they'd resend on retry).
COMMIT_EVERY = 100


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
        "scheduled_at": str(doc.scheduled_at) if doc.scheduled_at else None,
        "email_width": getattr(doc, "email_width", None) or 600,
        "blocks": json.loads(doc.blocks_json) if doc.blocks_json else [],
        "recipient_config": _load_recipient_config(doc),
    }


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


@frappe.whitelist()
def save_campaign(name=None, title=None, subject=None, preview_text=None, blocks=None, email_width=None, recipient_config=None):
    blocks_json = json.dumps(blocks if isinstance(blocks, list) else json.loads(blocks or "[]"))
    normalized_config = _normalize_recipient_config(recipient_config)

    if name:
        doc = frappe.get_doc("Letters Campaign", name)
        frappe.has_permission("Letters Campaign", "write", doc=doc, throw=True)
        if title is not None:
            doc.title = title
        if subject is not None:
            doc.subject = subject
        if preview_text is not None:
            doc.preview_text = preview_text
        if email_width is not None:
            try:
                doc.email_width = int(email_width)
            except (AttributeError, TypeError, ValueError):
                pass
        if normalized_config is not None:
            doc.recipient_config = normalized_config
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
            "email_width": int(email_width) if email_width else 600,
            "blocks_json": blocks_json,
            "recipient_config": normalized_config or "",
        })
        doc.insert()

    return {"name": doc.name, "title": doc.title, "status": doc.status}


@frappe.whitelist()
def render_preview(name=None, blocks=None, preview_text=None, email_width=None):
    """Compile blocks to email-safe HTML."""
    from letters.letters.utils.email_compiler import EmailCompiler

    if name and not blocks:
        doc = frappe.get_doc("Letters Campaign", name)
        frappe.has_permission("Letters Campaign", "read", doc=doc, throw=True)
        blocks_data = doc.blocks_json or "[]"
        if preview_text is None:
            preview_text = doc.preview_text
        if email_width is None:
            email_width = getattr(doc, "email_width", None) or 600
    else:
        blocks_data = blocks if isinstance(blocks, list) else json.loads(blocks or "[]")

    try:
        compiler = EmailCompiler(blocks_data, preview_text=preview_text or "", email_width=email_width or 600)
        html = compiler.compile()
        return {"html": html}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Letters render_preview error")
        frappe.throw(str(e))


def _is_email_field(df):
    """Frappe has no dedicated 'Email' fieldtype on most versions; email fields are
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
        "email_width": getattr(original, "email_width", None) or 600,
        "blocks_json": original.blocks_json or "[]",
        "recipient_config": getattr(original, "recipient_config", None) or "",
    })
    new_doc.insert()
    frappe.db.commit()
    return {"name": new_doc.name, "title": new_doc.title}


@frappe.whitelist()
def send_test(blocks=None, subject=None, preview_text=None, name=None, recipient=None, email_width=None):
    """Send a test email to the given recipient (defaults to the logged-in user)."""
    from letters.letters.utils.email_compiler import EmailCompiler

    if name and not blocks:
        doc = frappe.get_doc("Letters Campaign", name)
        frappe.has_permission("Letters Campaign", "read", doc=doc, throw=True)
        blocks_data = doc.blocks_json or "[]"
        subject = subject or doc.subject
        preview_text = preview_text or doc.preview_text
        if email_width is None:
            email_width = getattr(doc, "email_width", None) or 600
    else:
        blocks_data = blocks if isinstance(blocks, list) else json.loads(blocks or "[]")

    try:
        compiler = EmailCompiler(blocks_data, preview_text=preview_text or "", email_width=email_width or 600)
        html = compiler.compile()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Letters send_test compile error")
        frappe.throw(str(e))

    email = (recipient or "").strip() or frappe.session.user
    if not frappe.utils.validate_email_address(email, throw=False):
        frappe.throw(_("Please enter a valid email address to send the test to."))
    test_subject = f"[TEST] {subject or 'Email Preview'}"

    # Queue rather than send inline (now=False): a slow SMTP server must not
    # block the web request. The email queue worker delivers it shortly.
    frappe.sendmail(
        recipients=[email],
        subject=test_subject,
        message=html,
        now=False,
    )
    return {"sent_to": email}


# ── Open tracking & analytics ─────────────────────────────────────────────────

@frappe.whitelist(allow_guest=True)
def track_open(recipient_email=None, reference_name=None, reference_doctype=None, **kwargs):
    """Tracking-pixel endpoint: record an email open, then return a 1x1 gif.

    Frappe's email queue generates and *signs* this URL (via email_read_tracker_url),
    so we verify the signature before trusting the params. A pixel is always
    returned, even on failure, so the email never shows a broken image. Opens
    only register when the site is publicly reachable.
    """
    from frappe.utils.verified_command import verify_request

    try:
        if frappe.in_test or verify_request():
            if reference_doctype == "Letters Campaign" and reference_name and recipient_email:
                _record_open(reference_name, recipient_email)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Letters track_open error")

    frappe.response.update(frappe.utils.get_imaginary_pixel_response())


def _record_open(campaign_name, email):
    """Mark this campaign's recipient row(s) for `email` as opened. First open
    stamps opened_on; every hit increments open_count."""
    sends = frappe.get_all("Email Send", filters={"campaign": campaign_name}, pluck="name")
    if not sends:
        return
    rows = frappe.get_all(
        "Email Send Recipient",
        filters={"parent": ["in", sends], "email": email},
        fields=["name", "opened", "open_count"],
    )
    for r in rows:
        update = {"open_count": (r.open_count or 0) + 1}
        if not r.opened:
            update["opened"] = 1
            update["opened_on"] = frappe.utils.now_datetime()
        frappe.db.set_value("Email Send Recipient", r.name, update, update_modified=False)
    frappe.db.commit()


@frappe.whitelist()
def get_campaign_analytics(name):
    """Open-rate analytics for a campaign, aggregated over its recipient rows."""
    doc = frappe.get_doc("Letters Campaign", name)
    frappe.has_permission("Letters Campaign", "read", doc=doc, throw=True)

    sends = frappe.get_all(
        "Email Send",
        filters={"campaign": name},
        fields=["name", "status", "total_recipients", "sent_count", "creation"],
        order_by="creation desc",
    )
    if not sends:
        return {
            "sent_status": None, "total": 0, "sent": 0, "opened": 0,
            "open_rate": 0, "last_opened": None, "last_sent": None,
        }

    send_names = [s.name for s in sends]
    total = sum((s.total_recipients or 0) for s in sends)
    sent  = sum((s.sent_count or 0) for s in sends)
    opened = frappe.db.count(
        "Email Send Recipient", {"parent": ["in", send_names], "opened": 1}
    )
    last_opened = frappe.db.get_value(
        "Email Send Recipient",
        {"parent": ["in", send_names], "opened": 1},
        "opened_on", order_by="opened_on desc",
    )
    # Per-recipient status breakdown from the most recent send
    latest_send = sends[0].name
    status_counts = {}
    for row in frappe.get_all(
        "Email Send Recipient",
        filters={"parent": latest_send},
        fields=["status"],
    ):
        s = row.status or "Pending"
        status_counts[s] = status_counts.get(s, 0) + 1

    return {
        "sent_status": sends[0].status,
        "total":       total,
        "sent":        sent,
        "opened":      opened,
        "open_rate":   round((opened / sent) * 100, 1) if sent else 0,
        "last_opened": str(last_opened) if last_opened else None,
        "last_sent":   str(sends[0].creation),
        "status_counts": status_counts,
    }


@frappe.whitelist()
def get_campaign_recipients(name, limit=200):
    """Return the list of recipients for the most recent send of a campaign."""
    doc = frappe.get_doc("Letters Campaign", name)
    frappe.has_permission("Letters Campaign", "read", doc=doc, throw=True)

    send = frappe.db.get_value(
        "Email Send", {"campaign": name}, "name", order_by="creation desc"
    )
    if not send:
        return []

    rows = frappe.get_all(
        "Email Send Recipient",
        filters={"parent": send},
        fields=["email", "status", "opened", "opened_on"],
        order_by="email asc",
        limit=int(limit),
    )
    return rows


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


@frappe.whitelist()
def get_send_progress(name):
    """Return live send progress for a campaign (polls from the frontend)."""
    doc = frappe.get_doc("Letters Campaign", name)
    frappe.has_permission("Letters Campaign", "read", doc=doc, throw=True)

    send = frappe.get_last_doc(
        "Email Send",
        filters={"campaign": name, "status": ["in", ["Sending", "Sent", "Failed", "Partial"]]},
        order_by="creation desc",
    ) if frappe.db.exists("Email Send", {"campaign": name, "status": ["in", ["Sending", "Sent", "Failed", "Partial"]]}) else None

    if not send:
        return {"status": "Queued", "sent": 0, "total": 0}

    return {
        "status": send.status,
        "sent": send.sent_count or 0,
        "total": send.total_recipients or 0,
    }


# Hard caps for the link checker. A campaign can legitimately contain many
# links, but we must bound how much server-side fetching a single client call
# can trigger (total request count + a wall-clock budget across all of them).
_LINK_CHECK_MAX_URLS = 50
_LINK_CHECK_TIMEOUT = 5  # per-request, seconds
_LINK_CHECK_TIME_BUDGET = 25  # total wall-clock across all requests, seconds


def _ip_is_public(ip):
    """True only for globally-routable unicast addresses. Rejects private,
    loopback, link-local (incl. 169.254.0.0/16 cloud metadata), multicast,
    reserved, and unspecified ranges (IPv4 and IPv6)."""
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def _resolve_safe_target(url):
    """Validate ``url`` for server-side fetching and resolve it to a single,
    pinned IP address.

    Returns ``(host, ip, port, scheme, error)``. When ``error`` is a non-None
    reason string the URL must NOT be fetched. On success ``ip`` is the exact
    address the caller must connect to — every address the host resolves to has
    been checked, and the connection is later made to this pinned IP (not a
    fresh lookup), which closes the DNS-rebinding (TOCTOU) window.

    Blocks: non-http(s) schemes, and any hostname where ANY resolved address is
    non-public (so a DNS name pointing partly at an internal IP is rejected)."""
    import ipaddress
    import socket
    from urllib.parse import urlsplit

    try:
        parts = urlsplit(url)
    except ValueError:
        return None, None, None, None, "invalid url"

    if parts.scheme not in ("http", "https"):
        return None, None, None, None, "unsupported scheme"

    host = parts.hostname
    if not host:
        return None, None, None, None, "no host"

    port = parts.port or (443 if parts.scheme == "https" else 80)

    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        return None, None, None, None, "dns resolution failed"

    pinned_ip = None
    for info in infos:
        ip_str = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return None, None, None, None, "unresolvable address"
        if not _ip_is_public(ip):
            # Reject the whole host if ANY address is non-public — a partially
            # internal result set is a classic rebinding trick.
            return None, None, None, None, "private or reserved address"
        if pinned_ip is None:
            pinned_ip = ip_str

    return host, pinned_ip, port, parts.scheme, None


def _url_safety_error(url):
    """Back-compat thin wrapper: just the error reason (None when safe)."""
    return _resolve_safe_target(url)[4]


def _head_pinned(url, timeout):
    """Issue a HEAD request to ``url`` connecting to the pre-validated pinned IP.

    Redirects are NOT followed (a 3xx Location could point back at an internal
    host); the raw status code is returned. TLS uses the original hostname for
    SNI and certificate verification even though the socket targets the pinned
    IP, so security is preserved without a second DNS lookup.

    Returns the HTTP status code (int). Raises on connection/HTTP errors."""
    import http.client
    import socket
    import ssl
    from urllib.parse import urlsplit

    host, ip, port, scheme, error = _resolve_safe_target(url)
    if error:
        raise ValueError(error)

    parts = urlsplit(url)
    path = parts.path or "/"
    if parts.query:
        path = f"{path}?{parts.query}"

    if scheme == "https":
        ctx = ssl.create_default_context()
        conn = http.client.HTTPSConnection(host, port=port, timeout=timeout, context=ctx)
    else:
        conn = http.client.HTTPConnection(host, port=port, timeout=timeout)

    # Pin the socket to the validated IP. We override the address the socket
    # connects to (the pinned IP) while leaving conn.host as the real hostname
    # so the Host header, SNI, and cert validation all use the hostname.
    def _connect():
        sock = socket.create_connection((ip, port), timeout)
        if scheme == "https":
            conn.sock = ctx.wrap_socket(sock, server_hostname=host)
        else:
            conn.sock = sock

    conn.connect = _connect
    try:
        conn.request("HEAD", path, headers={"User-Agent": "Mozilla/5.0", "Host": host})
        resp = conn.getresponse()
        return resp.status
    finally:
        conn.close()


@frappe.whitelist()
def check_links(blocks=None, name=None):
    """Extract all hrefs from compiled email HTML and check if they resolve.

    URLs are validated against an SSRF allowlist before any fetch: only public
    http(s) hosts are probed (see _resolve_safe_target). The probe connects to
    the exact IP that passed validation (no second DNS lookup), so DNS
    rebinding cannot redirect us to an internal host. Internal/loopback/cloud-
    metadata targets are reported as blocked, never requested."""
    import re
    import time

    if name:
        doc = frappe.get_doc("Letters Campaign", name)
        frappe.has_permission("Letters Campaign", "read", doc=doc, throw=True)
        blocks_data = json.loads(doc.blocks_json or "[]")
        preview_text = doc.preview_text or ""
        email_width = getattr(doc, "email_width", None) or 600
    else:
        if not blocks:
            frappe.throw(_("No blocks provided."))
        blocks_data = json.loads(blocks) if isinstance(blocks, str) else blocks
        preview_text = ""
        email_width = 600

    from .utils.email_compiler import EmailCompiler
    html = EmailCompiler(blocks_data, preview_text=preview_text, email_width=email_width).compile()

    urls = list(dict.fromkeys(re.findall(r'href=["\']([^"\'#][^"\']*)["\']', html)))
    results = []
    deadline = time.monotonic() + _LINK_CHECK_TIME_BUDGET
    checked = 0
    for url in urls:
        if not url.startswith("http"):
            results.append({"url": url, "status": "skipped", "code": None})
            continue
        if checked >= _LINK_CHECK_MAX_URLS or time.monotonic() >= deadline:
            results.append({"url": url, "status": "skipped", "code": None})
            continue

        # SSRF guard: never let a user-supplied URL make us probe an internal
        # host. Validate (scheme + resolved IP ranges) before any network call.
        if _url_safety_error(url):
            results.append({"url": url, "status": "blocked", "code": None})
            continue

        checked += 1
        try:
            code = _head_pinned(url, _LINK_CHECK_TIMEOUT)
            # Treat 4xx/5xx as broken; 2xx/3xx as reachable.
            if code >= 400:
                results.append({"url": url, "status": "error", "code": code})
            else:
                results.append({"url": url, "status": "ok", "code": code})
        except Exception:
            results.append({"url": url, "status": "error", "code": None})

    return results


@frappe.whitelist()
def schedule_campaign(name, scheduled_at):
    """Mark a campaign to be sent at a future datetime (ISO-8601 string, server timezone)."""
    doc = frappe.get_doc("Letters Campaign", name)
    frappe.has_permission("Letters Campaign", "write", doc=doc, throw=True)

    if doc.status in ("Sent", "Sending"):
        frappe.throw(_("This campaign has already been sent or is currently sending."))

    if not doc.blocks_json:
        frappe.throw(_("Campaign has no content to send."))
    if not doc.subject:
        frappe.throw(_("Campaign has no subject line."))

    # A scheduled send runs with no UI present, so the audience must already be
    # saved on the campaign — otherwise the send would silently have no one to
    # go to when it fires.
    recip = _recipient_args_from_config(doc)
    if not any(recip):
        frappe.throw(_("Choose recipients before scheduling this campaign."))

    from frappe.utils import get_datetime
    dt = get_datetime(scheduled_at)
    if dt <= frappe.utils.now_datetime():
        frappe.throw(_("Scheduled time must be in the future."))

    doc.db_set("scheduled_at", dt)
    doc.db_set("status", "Scheduled")
    frappe.db.commit()
    return {"scheduled_at": str(dt)}


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

    # Idempotency guard — a fully-sent or in-flight campaign cannot be re-sent.
    if doc.status in ("Sent", "Sending"):
        frappe.throw(_("This campaign has already been sent or is currently sending."))

    if not doc.blocks_json:
        frappe.throw(_("Campaign has no content to send."))
    if not doc.subject:
        frappe.throw(_("Campaign has no subject line."))

    # ── Resume a previous partial/failed send instead of starting over ───────
    # Per-recipient state lives on the Email Send doc, so a retry re-runs the
    # same job; _execute_send skips recipients already marked Sent. This is what
    # prevents a failed batch from re-delivering to everyone on retry.
    existing = frappe.get_all(
        "Email Send",
        filters={"campaign": name},
        fields=["name", "status"],
        order_by="creation desc",
        limit=1,
    )
    if existing and existing[0].status in ("Failed", "Partial"):
        return _resume_send(existing[0].name, name, doc)

    # ── Fall back to the campaign's saved audience when no explicit source ───
    # is passed. Scheduled sends (process_scheduled_sends) and any server-side
    # caller rely on this: the recipient selection is persisted on the campaign
    # so the send no longer depends on transient UI state.
    if not (email_group or doctype_config or recipients):
        recipients, email_group, doctype_config = _recipient_args_from_config(doc)
        if not (email_group or doctype_config or recipients):
            frappe.throw(_("This campaign has no saved recipients. Open it and choose an audience before sending."))

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

    # ── Honour unsubscribes before sending ───────────────────────────────────
    suppressed = _suppressed_emails()
    if suppressed:
        recipient_list = [e for e in recipient_list if e not in suppressed]
    if not recipient_list:
        frappe.throw(_("All selected recipients have unsubscribed from this campaign."))

    # ── Drop malformed addresses (server-side, regardless of client) ─────────
    recipient_list, invalid_count = _valid_emails(recipient_list)
    if not recipient_list:
        frappe.throw(_("No valid email addresses to send to."))

    # ── Guard against an oversized audience (no silent truncation) ───────────
    if len(recipient_list) > MAX_RECIPIENTS:
        frappe.throw(_(
            "This audience has more than {0} recipients, which is above the "
            "per-campaign limit. Narrow your filters or split the send."
        ).format(MAX_RECIPIENTS))

    # ── Claim the send synchronously to prevent a race between two requests ──
    # Each recipient becomes a child row with its own status, so the background
    # job (and any later retry) can track delivery per address.
    send_doc = frappe.get_doc({
        "doctype": "Email Send",
        "campaign": name,
        "status": "Sending",
        "send_mode": mode,
        "email_group": email_group or "",
        "total_recipients": len(recipient_list),
        "sent_count": 0,
        "recipients": [{"email": e, "status": "Pending"} for e in recipient_list],
    })
    send_doc.insert(ignore_permissions=True)
    frappe.db.commit()  # flush so the background job can read the send_doc

    # Mark campaign as Sending before returning so any re-submit attempt is blocked
    doc.status = "Sending"
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    _enqueue_send(send_doc.name, name)
    return {
        "queued": True,
        "count": len(recipient_list),
        "mode": mode,
        "skipped_invalid": invalid_count,
    }


def _resume_send(send_doc_name, campaign_name, campaign_doc):
    """Re-enqueue a partial/failed Email Send. Only its unsent recipients will
    be (re)attempted, so retrying never re-delivers to addresses already Sent."""
    unsent = frappe.db.count(
        "Email Send Recipient",
        {"parent": send_doc_name, "status": ["!=", "Sent"]},
    )
    frappe.db.set_value("Email Send", send_doc_name, "status", "Sending")
    campaign_doc.status = "Sending"
    campaign_doc.save(ignore_permissions=True)
    frappe.db.commit()

    _enqueue_send(send_doc_name, campaign_name)
    return {"queued": True, "count": unsent, "resumed": True}


def _enqueue_send(send_doc_name, campaign_name):
    """Enqueue the per-recipient delivery loop as a background job."""
    frappe.enqueue(
        "letters.letters.api._execute_send",
        queue="long",
        timeout=SEND_JOB_TIMEOUT,
        job_name=f"letters_send_{campaign_name}",
        send_doc_name=send_doc_name,
        campaign_name=campaign_name,
    )


def _execute_send(send_doc_name, campaign_name):
    """
    Background job: compile the campaign and send one email per recipient,
    recording delivery status on each recipient row. Recipients already marked
    Sent are skipped, so a retry resumes from where a previous run stopped.

    Runs in a worker process; must NOT be decorated with @frappe.whitelist().
    """
    try:
        doc = frappe.get_doc("Letters Campaign", campaign_name)
        send_doc = frappe.get_doc("Email Send", send_doc_name)

        from letters.letters.utils.email_compiler import EmailCompiler
        compiler = EmailCompiler(doc.blocks_json, preview_text=doc.preview_text, email_width=getattr(doc, "email_width", None) or 600)
        html = compiler.compile()

        sent = failed = 0
        for idx, row in enumerate(send_doc.recipients):
            if row.status == "Sent":
                sent += 1
                continue

            try:
                # Setting a reference doc makes Frappe inject a signed
                # unsubscribe footer (with a guest confirmation page) and
                # auto-suppress Email Unsubscribe matches — for every send mode,
                # not just Email Groups. Recipients already opted out were
                # filtered in send_campaign via _suppressed_emails().
                frappe.sendmail(
                    recipients=[row.email],
                    subject=doc.subject,
                    message=html,
                    now=False,
                    reference_doctype="Letters Campaign",
                    reference_name=campaign_name,
                    # Frappe injects a per-recipient tracking pixel pointing here
                    # (with signed recipient_email/reference params) so opens can
                    # be recorded. Only registers when the site is publicly
                    # reachable — a localhost pixel never loads.
                    email_read_tracker_url="/api/method/letters.letters.api.track_open",
                )
                row.status = "Sent"
                frappe.db.set_value(
                    "Email Send Recipient", row.name, "status", "Sent",
                    update_modified=False,
                )
                sent += 1
            except Exception as e:
                row.status = "Failed"
                frappe.db.set_value(
                    "Email Send Recipient", row.name,
                    {"status": "Failed", "error_message": str(e)[:500]},
                    update_modified=False,
                )
                failed += 1
                frappe.log_error(frappe.get_traceback(), "Letters recipient send error")

            # Periodically flush so a worker crash doesn't lose progress.
            if (idx + 1) % COMMIT_EVERY == 0:
                frappe.db.commit()

        # ── Finalise: derive the batch outcome from per-recipient results ────
        if failed == 0:
            send_status = campaign_status = "Sent"
        elif sent == 0:
            send_status = campaign_status = "Failed"
        else:
            send_status, campaign_status = "Partial", "Failed"

        send_doc.status = send_status
        send_doc.sent_count = sent
        send_doc.save(ignore_permissions=True)
        doc.status = campaign_status
        doc.save(ignore_permissions=True)
        frappe.db.commit()

    except Exception:
        # A failure here is the whole batch (e.g. compile error), not one
        # recipient. Mark Failed (not Draft) so a retry resumes rather than
        # re-delivering to everyone.
        frappe.log_error(frappe.get_traceback(), "Letters _execute_send error")
        try:
            frappe.db.set_value("Email Send", send_doc_name, "status", "Failed")
            frappe.db.set_value("Letters Campaign", campaign_name, "status", "Failed")
            frappe.db.commit()
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Letters _execute_send cleanup error")


def process_scheduled_sends():
    """Scheduled task: fire any campaigns whose scheduled_at has passed."""
    from frappe.utils import now_datetime
    due = frappe.get_all(
        "Letters Campaign",
        filters={"status": "Scheduled", "scheduled_at": ["<=", now_datetime()]},
        fields=["name"],
    )
    for row in due:
        try:
            doc = frappe.get_doc("Letters Campaign", row.name)
            # Reset to Draft so send_campaign's idempotency guard passes
            doc.db_set("status", "Draft")
            frappe.db.commit()
            send_campaign(row.name)
        except Exception:
            # The send didn't start (e.g. no saved recipients, compile error).
            # Mark Failed rather than leaving it silently reverted to Draft, so
            # the failure is visible and the user can fix and retry.
            frappe.log_error(frappe.get_traceback(), f"Letters scheduled send error: {row.name}")
            try:
                frappe.db.set_value("Letters Campaign", row.name, "status", "Failed")
                frappe.db.commit()
            except Exception:
                frappe.log_error(frappe.get_traceback(), f"Letters scheduled send cleanup error: {row.name}")
