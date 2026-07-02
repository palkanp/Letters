from __future__ import annotations

# Public API surface. api.py was split into feature modules; everything is
# re-exported here so existing dotted paths ("letters.letters.api.<name>"),
# whitelist registration, enqueue strings, and the scheduler keep resolving.

from .recipients import (
    get_doctypes_with_email_fields,
    get_email_fields,
    get_doctype_filter_fields,
    count_doctype_recipients,
    get_email_groups,
    create_email_group_from_source,
    _is_email_field,
    _load_recipient_config,
    _normalize_recipient_config,
    _recipient_args_from_config,
    _has_recipient_config,
    _resolve_single_source_emails,
    _resolve_multi_source,
    _suppressed_emails,
    _valid_emails,
)
from .letters_api import (
    get_letter,
    save_letter,
    get_letters,
    get_templates,
    render_preview,
    duplicate_letter,
    _unique_letter_title,
)
from .sending import (
    MAX_RECIPIENTS,
    SEND_JOB_TIMEOUT,
    send_test,
    track_open,
    get_letter_analytics,
    get_letter_recipients,
    get_send_progress,
    schedule_letter,
    send_letter,
    process_scheduled_sends,
    reconcile_active_sends,
    _record_open,
    _resume_send,
    _bulk_insert_recipients,
    _enqueue_send,
    _execute_send,
)
from .unsubscribe import (
    unsubscribe_redirect,
    save_preferences,
)
from .links import (
    check_links,
    start_link_check,
    get_link_check_result,
    _ip_is_public,
    _resolve_safe_target,
    _url_safety_error,
    _head_pinned,
    _run_link_check,
    _resolve_link_check_args,
    _link_check_worker,
)
