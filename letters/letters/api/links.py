from __future__ import annotations

import json

import frappe
from frappe import _




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




def _run_link_check(blocks_data, preview_text, email_width):
    """Core probe loop. Compiles the email and HEAD-checks every href.

    URLs are validated against an SSRF allowlist before any fetch: only public
    http(s) hosts are probed (see _resolve_safe_target). The probe connects to
    the exact IP that passed validation (no second DNS lookup), so DNS
    rebinding cannot redirect us to an internal host. Internal/loopback/cloud-
    metadata targets are reported as blocked, never requested."""
    import re
    import time

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

        if _url_safety_error(url):
            results.append({"url": url, "status": "blocked", "code": None})
            continue

        checked += 1
        try:
            code = _head_pinned(url, _LINK_CHECK_TIMEOUT)
            if code >= 400:
                results.append({"url": url, "status": "error", "code": code})
            else:
                results.append({"url": url, "status": "ok", "code": code})
        except Exception:
            results.append({"url": url, "status": "error", "code": None})

    return results




def _resolve_link_check_args(blocks, name):
    """Shared input resolution for sync and async link-check paths."""
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
    return blocks_data, preview_text, email_width




@frappe.whitelist(methods=["GET", "POST"])
def check_links(blocks: str | None = None, name: str | None = None):
    """Synchronous link check (used by tests and the CLI). Prefer
    start_link_check / get_link_check_result in the UI to avoid tying
    up a web worker for the full probe duration."""
    blocks_data, preview_text, email_width = _resolve_link_check_args(blocks, name)
    return _run_link_check(blocks_data, preview_text, email_width)




@frappe.whitelist(methods=["POST"])
def start_link_check(blocks: str | None = None, name: str | None = None):
    """Enqueue a background link check and return a job key the caller
    can poll with get_link_check_result. The result is cached for 5 min."""
    blocks_data, preview_text, email_width = _resolve_link_check_args(blocks, name)
    job_key = frappe.generate_hash(length=20)
    frappe.enqueue(
        "letters.letters.api._link_check_worker",
        queue="short",
        timeout=120,
        blocks_json=json.dumps(blocks_data),
        preview_text=preview_text,
        email_width=email_width,
        job_key=job_key,
    )
    return {"job_key": job_key}




@frappe.whitelist(methods=["GET", "POST"])
def get_link_check_result(job_key: str):
    """Return {"status": "pending"} or {"status": "done", "results": [...]}."""
    result = frappe.cache().get_value(f"link_check:{job_key}")
    if result is None:
        return {"status": "pending"}
    return {"status": "done", "results": result}




def _link_check_worker(blocks_json, preview_text, email_width, job_key):
    """Background worker: runs the probe loop and writes results to cache."""
    blocks_data = json.loads(blocks_json)
    results = _run_link_check(blocks_data, preview_text, int(email_width))
    frappe.cache().set_value(f"link_check:{job_key}", results, expires_in_sec=300)
