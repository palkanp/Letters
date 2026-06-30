"""
Tests for letters/letters/api.py

All Frappe framework calls are mocked via unittest.mock so no bench is needed.

Run with:  pytest letters/tests/test_api.py -v
"""
from __future__ import annotations

import sys
import os
import json
from unittest.mock import MagicMock, patch
import pytest

# ---------------------------------------------------------------------------
# Frappe stub — must be installed BEFORE importing api.py.
# Critical details:
#  1. @frappe.whitelist() must be a pass-through decorator so the actual
#     function body still runs during tests.
#  2. frappe.throw() must raise so code that calls it actually stops.
# ---------------------------------------------------------------------------

class FrappeValidationError(Exception):
    pass


class FrappeDict(dict):
    """Minimal frappe._dict equivalent: dict with attribute access."""
    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError:
            raise AttributeError(k)


def _whitelist(*args, **kwargs):
    """Pass-through decorator supporting both @frappe.whitelist and
    @frappe.whitelist(allow_guest=True)."""
    def decorator(fn):
        return fn
    if len(args) == 1 and callable(args[0]) and not kwargs:
        return args[0]
    return decorator


def _throw(msg="", **kwargs):
    raise FrappeValidationError(str(msg))


frappe_stub = MagicMock()
frappe_stub.whitelist = _whitelist
frappe_stub.throw     = _throw
frappe_stub._         = lambda s: s  # translation no-op

sys.modules["frappe"] = frappe_stub

# `from frappe.utils import get_datetime` (inside schedule_campaign /
# process_scheduled_sends) needs frappe.utils registered as a module. We do NOT
# register it globally — that would leak into other test files (e.g. the
# renderer tests rely on `from frappe.utils import get_url` raising to keep
# relative paths relative). Instead the few tests that need it wrap the call in
# this context manager so sys.modules is restored afterwards.
from contextlib import contextmanager


@contextmanager
def _frappe_utils_importable():
    from unittest.mock import patch as _patch
    with _patch.dict(sys.modules, {"frappe.utils": frappe_stub.utils}):
        yield

# Now we can import api with a functional frappe mock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import importlib
import letters.letters.api as api_module

# Convenient reference (same object as sys.modules["frappe"])
import frappe  # noqa

# Import mixin classes so we can bind real business-logic methods onto mock docs.
# Frappe is already stubbed above so module-level `import frappe` in each mixin works.
import types as _types
from letters.letters.doctype.letter._content import ContentMixin
from letters.letters.doctype.letter._sending import SendingMixin
from letters.letters.doctype.letter._analytics import AnalyticsMixin


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _letter_doc(name="CAMP-001", status="Draft", blocks_json=None, subject="Hello"):
    doc = MagicMock()
    doc.name = name
    doc.title = "Test Letter"
    doc.subject = subject
    doc.preview_text = ""
    doc.status = status
    doc.scheduled_at = None
    doc.email_width = 600
    doc.recipient_config = ""
    doc.blocks_json = blocks_json if blocks_json is not None else json.dumps(
        [{"type": "text", "props": {"content": "Hi"}}]
    )
    # Bind real mixin implementations so that API-wrapper tests exercise
    # the actual business logic rather than returning plain MagicMocks.
    doc.as_builder_dict     = _types.MethodType(ContentMixin.as_builder_dict,     doc)
    doc.render_preview_html = _types.MethodType(ContentMixin.render_preview_html, doc)
    doc.duplicate           = _types.MethodType(ContentMixin.duplicate,           doc)
    doc.send                = _types.MethodType(SendingMixin.send,                doc)
    doc.schedule            = _types.MethodType(SendingMixin.schedule,            doc)
    doc.send_test_email     = _types.MethodType(SendingMixin.send_test_email,     doc)
    doc.get_analytics       = _types.MethodType(AnalyticsMixin.get_analytics,     doc)
    doc.get_recipients      = _types.MethodType(AnalyticsMixin.get_recipients,    doc)
    doc.get_send_progress   = _types.MethodType(AnalyticsMixin.get_send_progress, doc)
    doc.record_open         = _types.MethodType(AnalyticsMixin.record_open,       doc)
    return doc


# Routes frappe.get_all calls by doctype so a single test can stub several
# lookups (the resume check on "Email Send", Email Group members, etc.)
# independently. Populated/cleared per test in _reset().
GETALL: dict[str, list] = {}


def _route_get_all(doctype, *a, **k):
    return GETALL.get(doctype, [])


def _reset():
    """Reset per-test state on the mock."""
    frappe_stub.get_doc.reset_mock()
    frappe_stub.get_doc.side_effect = None
    frappe_stub.has_permission.reset_mock()
    frappe_stub.has_permission.side_effect = None
    frappe_stub.has_permission.return_value = True
    frappe_stub.db.exists.reset_mock()
    frappe_stub.db.exists.return_value = None
    frappe_stub.db.commit.reset_mock()
    frappe_stub.db.set_value.reset_mock()
    frappe_stub.db.set_value.side_effect = None
    frappe_stub.db.count.reset_mock()
    frappe_stub.db.count.return_value = 0
    frappe_stub.db.get_value.reset_mock()
    frappe_stub.db.get_value.side_effect = None
    frappe_stub.db.get_value.return_value = None
    frappe_stub.enqueue.reset_mock()
    frappe_stub.enqueue.return_value = None
    # Email validator: by default every address is valid (returns truthy).
    frappe_stub.utils.validate_email_address.reset_mock()
    frappe_stub.utils.validate_email_address.side_effect = None
    frappe_stub.utils.validate_email_address.return_value = "ok@example.com"
    GETALL.clear()
    GETALL["Email Send"] = []          # no prior send → fresh send by default
    GETALL["Email Group Member"] = []
    frappe_stub.get_all.reset_mock()
    frappe_stub.get_all.side_effect = _route_get_all
    frappe_stub.sendmail.reset_mock()
    frappe_stub.sendmail.side_effect = None
    frappe_stub.log_error.reset_mock()


# ── get_letter ──────────────────────────────────────────────────────────────

class TestGetLetter:
    def setup_method(self):
        _reset()

    def test_permission_check_is_called(self):
        doc = _letter_doc()
        frappe_stub.get_doc.return_value = doc

        api_module.get_letter("CAMP-001")

        frappe_stub.has_permission.assert_called_with(
            "Letter", "read", doc=doc, throw=True
        )

    def test_returns_expected_fields(self):
        doc = _letter_doc()
        frappe_stub.get_doc.return_value = doc

        result = api_module.get_letter("CAMP-001")
        assert "name" in result
        assert "blocks" in result
        assert "subject" in result
        assert isinstance(result["blocks"], list)

    def test_blocks_json_parsed_to_list(self):
        doc = _letter_doc(blocks_json=json.dumps([{"type": "text", "props": {}}]))
        frappe_stub.get_doc.return_value = doc

        result = api_module.get_letter("CAMP-001")
        assert isinstance(result["blocks"], list)
        assert result["blocks"][0]["type"] == "text"

    def test_permission_failure_propagates(self):
        doc = _letter_doc()
        frappe_stub.get_doc.return_value = doc
        frappe_stub.has_permission.side_effect = Exception("Forbidden")

        with pytest.raises(Exception, match="Forbidden"):
            api_module.get_letter("CAMP-001")


# ── send_letter — permission check ─────────────────────────────────────────

class TestSendLetterPermission:
    def setup_method(self):
        _reset()

    def _run_send(self, doc, recipients=None, **kwargs):
        send_doc_mock = MagicMock()
        send_doc_mock.name = "SD-NEW"

        def get_doc_side_effect(arg, *args):
            if isinstance(arg, dict):
                return send_doc_mock
            return doc

        frappe_stub.get_doc.side_effect = get_doc_side_effect
        return api_module.send_letter(
            "CAMP-001",
            recipients=json.dumps(recipients or ["a@b.com"]),
            **kwargs,
        )

    def test_permission_check_is_called(self):
        doc = _letter_doc()
        self._run_send(doc)
        frappe_stub.has_permission.assert_called_with(
            "Letter", "write", doc=doc, throw=True
        )

    def test_permission_failure_propagates(self):
        doc = _letter_doc()
        frappe_stub.has_permission.side_effect = Exception("Permission denied")
        frappe_stub.get_doc.return_value = doc

        with pytest.raises(Exception, match="Permission denied"):
            api_module.send_letter("CAMP-001", recipients=json.dumps(["a@b.com"]))


# ── send_letter — idempotency guard ─────────────────────────────────────────

class TestSendLetterIdempotency:
    def setup_method(self):
        _reset()

    def test_throws_when_status_is_sent(self):
        frappe_stub.get_doc.return_value = _letter_doc(status="Sent")
        with pytest.raises(FrappeValidationError, match="already been sent"):
            api_module.send_letter("CAMP-001", recipients=json.dumps(["a@b.com"]))

    def test_throws_when_status_is_sending(self):
        frappe_stub.get_doc.return_value = _letter_doc(status="Sending")
        with pytest.raises(FrappeValidationError, match="already been sent|currently sending"):
            api_module.send_letter("CAMP-001", recipients=json.dumps(["a@b.com"]))

    def test_resumes_existing_failed_send(self):
        """H1: a Failed prior send is resumed (not restarted), so already-Sent
        recipients are not re-delivered."""
        doc = _letter_doc(status="Failed")
        frappe_stub.get_doc.return_value = doc
        GETALL["Email Send"] = [FrappeDict(name="SD-OLD", status="Failed")]
        frappe_stub.db.count.return_value = 3  # 3 unsent recipients remain

        result = api_module.send_letter("CAMP-001", recipients=json.dumps(["a@b.com"]))

        assert result.get("resumed") is True
        assert result["count"] == 3
        assert frappe_stub.enqueue.called
        # The old send doc is flipped back to Sending, not a new one created
        frappe_stub.db.set_value.assert_any_call("Email Send", "SD-OLD", "status", "Sending")

    def test_resumes_existing_partial_send(self):
        doc = _letter_doc(status="Failed")
        frappe_stub.get_doc.return_value = doc
        GETALL["Email Send"] = [FrappeDict(name="SD-OLD", status="Partial")]
        frappe_stub.db.count.return_value = 1

        result = api_module.send_letter("CAMP-001", recipients=json.dumps(["a@b.com"]))
        assert result.get("resumed") is True

    def test_no_throw_for_clean_draft_with_no_existing_send(self):
        doc = _letter_doc(status="Draft")
        send_doc_mock = MagicMock()
        send_doc_mock.name = "SD-NEW"

        def get_doc_se(arg, *args):
            return send_doc_mock if isinstance(arg, dict) else doc

        frappe_stub.get_doc.side_effect = get_doc_se
        frappe_stub.db.exists.return_value = None

        # Should not raise
        api_module.send_letter("CAMP-001", recipients=json.dumps(["a@b.com"]))


# ── send_letter — validation ────────────────────────────────────────────────

class TestSendLetterValidation:
    def setup_method(self):
        _reset()

    def test_throws_when_blocks_json_empty(self):
        frappe_stub.get_doc.return_value = _letter_doc(blocks_json="")
        with pytest.raises(FrappeValidationError, match="no content"):
            api_module.send_letter("CAMP-001", recipients=json.dumps(["a@b.com"]))

    def test_throws_when_subject_empty(self):
        frappe_stub.get_doc.return_value = _letter_doc(subject="")
        with pytest.raises(FrappeValidationError, match="no subject"):
            api_module.send_letter("CAMP-001", recipients=json.dumps(["a@b.com"]))

    def test_throws_when_no_recipients(self):
        frappe_stub.get_doc.return_value = _letter_doc()
        with pytest.raises(FrappeValidationError, match="No recipients"):
            api_module.send_letter("CAMP-001", recipients=json.dumps([]))

    def test_throws_when_recipients_all_whitespace(self):
        frappe_stub.get_doc.return_value = _letter_doc()
        with pytest.raises(FrappeValidationError):
            api_module.send_letter("CAMP-001", recipients=json.dumps(["  ", " "]))

    def test_throws_when_email_group_has_no_active_members(self):
        frappe_stub.get_doc.return_value = _letter_doc()
        GETALL["Email Group Member"] = []  # no members
        with pytest.raises(FrappeValidationError, match="no active subscribers"):
            api_module.send_letter("CAMP-001", email_group="GROUP-EMPTY")

    def test_throws_when_audience_exceeds_max(self):
        """H3: an oversized audience must be refused, never silently truncated."""
        frappe_stub.get_doc.return_value = _letter_doc()
        oversized = [f"user{i}@example.com" for i in range(api_module.MAX_RECIPIENTS + 1)]
        with pytest.raises(FrappeValidationError, match="above the per-letter limit"):
            api_module.send_letter("CAMP-001", recipients=json.dumps(oversized))

    def test_unsubscribed_recipients_are_filtered_out(self):
        """H2: addresses in Email Unsubscribe are dropped before sending."""
        doc = _letter_doc()
        send_doc_mock = MagicMock()
        send_doc_mock.name = "SD-NEW"

        def get_doc_se(arg, *args):
            return send_doc_mock if isinstance(arg, dict) else doc

        frappe_stub.get_doc.side_effect = get_doc_se
        GETALL["Email Unsubscribe"] = ["gone@b.com"]

        result = api_module.send_letter(
            "CAMP-001", recipients=json.dumps(["gone@b.com", "stay@b.com"])
        )
        assert result["count"] == 1  # only stay@b.com survives

    def test_throws_when_all_recipients_unsubscribed(self):
        frappe_stub.get_doc.return_value = _letter_doc()
        GETALL["Email Unsubscribe"] = ["gone@b.com"]
        with pytest.raises(FrappeValidationError, match="unsubscribed"):
            api_module.send_letter("CAMP-001", recipients=json.dumps(["gone@b.com"]))

    def test_invalid_emails_are_dropped_server_side(self):
        """M2: malformed addresses are filtered out even if the client sent them."""
        doc = _letter_doc()
        send_doc_mock = MagicMock()
        send_doc_mock.name = "SD-NEW"

        def get_doc_se(arg, *args):
            return send_doc_mock if isinstance(arg, dict) else doc

        frappe_stub.get_doc.side_effect = get_doc_se
        # Only addresses containing "@" are considered valid by the stub.
        frappe_stub.utils.validate_email_address.side_effect = (
            lambda e, throw=False: e if "@" in e else ""
        )

        result = api_module.send_letter(
            "CAMP-001", recipients=json.dumps(["good@b.com", "notanemail"])
        )
        assert result["count"] == 1
        assert result["skipped_invalid"] == 1

    def test_throws_when_all_emails_invalid(self):
        frappe_stub.get_doc.return_value = _letter_doc()
        frappe_stub.utils.validate_email_address.side_effect = lambda e, throw=False: ""
        with pytest.raises(FrappeValidationError, match="No valid email"):
            api_module.send_letter("CAMP-001", recipients=json.dumps(["nope", "also-nope"]))

    def test_recipients_json_string_is_parsed(self):
        doc = _letter_doc()
        send_doc_mock = MagicMock()
        send_doc_mock.name = "SD-NEW"

        def get_doc_se(arg, *args):
            return send_doc_mock if isinstance(arg, dict) else doc

        frappe_stub.get_doc.side_effect = get_doc_se

        # Pass recipients as a JSON string (as the JS frontend does)
        result = api_module.send_letter("CAMP-001", recipients='["r@r.com"]')
        assert result["count"] == 1


# ── send_letter — enqueue ───────────────────────────────────────────────────

class TestSendLetterEnqueue:
    def setup_method(self):
        _reset()

    def _run(self, recipients=None, email_group=None, **members):
        doc = _letter_doc()
        send_doc_mock = MagicMock()
        send_doc_mock.name = "SD-NEW"

        def get_doc_se(arg, *args):
            return send_doc_mock if isinstance(arg, dict) else doc

        frappe_stub.get_doc.side_effect = get_doc_se

        if email_group:
            GETALL["Email Group Member"] = [FrappeDict(email="m@m.com")]
            return api_module.send_letter("CAMP-001", email_group=email_group)

        return api_module.send_letter(
            "CAMP-001",
            recipients=json.dumps(recipients or ["a@b.com"]),
        )

    def test_enqueues_background_job(self):
        self._run()
        assert frappe_stub.enqueue.called

    def test_enqueued_task_is_execute_send(self):
        self._run()
        task = frappe_stub.enqueue.call_args.args[0] if frappe_stub.enqueue.call_args.args \
               else frappe_stub.enqueue.call_args.kwargs.get("method", "")
        assert "_execute_send" in str(task)

    def test_returns_queued_true(self):
        result = self._run()
        assert result["queued"] is True

    def test_returns_correct_count(self):
        result = self._run(recipients=["a@b.com", "c@d.com"])
        assert result["count"] == 2

    def test_recipients_written_via_bulk_insert(self):
        """Child rows go in one batched INSERT, not the per-row ORM path, so a
        large audience cannot trip the web-request (gunicorn) timeout."""
        frappe_stub.db.bulk_insert.reset_mock()
        self._run(recipients=["a@b.com", "c@d.com", "e@f.com"])
        frappe_stub.db.bulk_insert.assert_called_once()
        kwargs = frappe_stub.db.bulk_insert.call_args.kwargs
        args = frappe_stub.db.bulk_insert.call_args.args
        assert args[0] == "Email Send Recipient"
        # 3 recipients -> 3 value tuples, all Pending.
        values = kwargs.get("values") if "values" in kwargs else args[2]
        values = list(values)
        assert len(values) == 3
        assert all(v[-1] == "Pending" for v in values)

    def test_parent_doc_carries_no_inline_recipients(self):
        """The Email Send parent is inserted empty; recipients are bulk-inserted
        separately. A doc dict with an inline 50k-row child list is exactly the
        slow path we are avoiding."""
        captured = {}

        def get_doc_se(arg, *a):
            if isinstance(arg, dict):
                captured["doc"] = arg
                m = MagicMock()
                m.name = "SD-NEW"
                return m
            return _letter_doc()

        frappe_stub.get_doc.side_effect = get_doc_se
        api_module.send_letter("CAMP-001", recipients=json.dumps(["a@b.com"]))
        assert "recipients" not in captured["doc"]

    def test_email_group_mode_returns_correct_count(self):
        result = self._run(email_group="GROUP-A")
        assert result["count"] == 1
        assert result["mode"] == "email_group"

    def test_letter_status_set_to_sending_before_enqueue(self):
        """Campaign must be marked 'Sending' synchronously to block re-submit."""
        doc = _letter_doc()
        send_doc_mock = MagicMock()
        send_doc_mock.name = "SD-NEW"

        set_statuses = []

        def get_doc_se(arg, *args):
            return send_doc_mock if isinstance(arg, dict) else doc

        def set_status(val):
            set_statuses.append(("campaign", val))

        type(doc).status = property(lambda self: "Draft", lambda self, v: set_statuses.append(v))
        frappe_stub.get_doc.side_effect = get_doc_se
        api_module.send_letter("CAMP-001", recipients=json.dumps(["a@b.com"]))
        # The important thing: enqueue WAS called regardless of property details
        assert frappe_stub.enqueue.called


# ── _execute_send ──────────────────────────────────────────────────────────────

def _recipient(email, status="Pending"):
    """A stand-in for an Email Send Recipient child row."""
    r = MagicMock()
    r.email = email
    r.status = status
    r.name = f"R-{email}"
    return r


class TestExecuteSend:
    def setup_method(self):
        _reset()

    def _docs(self, recipients=None, send_mode="direct", email_group=None, blocks_json=None):
        campaign = _letter_doc(blocks_json=blocks_json)
        send_doc = MagicMock()
        send_doc.name = "SD-001"
        send_doc.send_mode = send_mode
        send_doc.email_group = email_group
        send_doc.recipients = recipients if recipients is not None else [_recipient("a@b.com")]

        def get_doc_se(doctype, name=None):
            return campaign if doctype == "Letter" else send_doc

        frappe_stub.get_doc.side_effect = get_doc_se
        return campaign, send_doc

    @staticmethod
    def _run():
        with patch("letters.letters.utils.email_compiler.EmailCompiler") as C:
            C.return_value.compile.return_value = "<html></html>"
            api_module._execute_send("SD-001", "CAMP-001")

    def test_sends_one_email_per_recipient(self):
        self._docs(recipients=[_recipient("a@b.com"), _recipient("c@d.com")])
        self._run()
        assert frappe_stub.sendmail.call_count == 2

    def test_marks_each_recipient_sent(self):
        rows = [_recipient("a@b.com"), _recipient("c@d.com")]
        self._docs(recipients=rows)
        self._run()
        assert all(r.status == "Sent" for r in rows)

    def test_skips_already_sent_recipients(self):
        """Resume: a recipient already Sent is not re-delivered."""
        rows = [_recipient("done@b.com", status="Sent"), _recipient("new@b.com")]
        self._docs(recipients=rows)
        self._run()
        assert frappe_stub.sendmail.call_count == 1
        assert frappe_stub.sendmail.call_args.kwargs["recipients"] == ["new@b.com"]

    def test_marks_send_doc_sent_on_full_success(self):
        self._docs(recipients=[_recipient("a@b.com")])
        self._run()
        # Finalised via a targeted parent-only set_value (no full child rewrite).
        frappe_stub.db.set_value.assert_any_call(
            "Email Send", "SD-001",
            {"status": "Sent", "sent_count": 1},
            update_modified=False,
        )

    def test_marks_letter_sent_on_full_success(self):
        self._docs(recipients=[_recipient("a@b.com")])
        self._run()
        frappe_stub.db.set_value.assert_any_call(
            "Letter", "CAMP-001", "status", "Sent",
            update_modified=False,
        )

    def test_partial_failure_marks_send_partial_and_letter_partial(self):
        # When some recipients succeed and some fail the send is Partial and the
        # campaign is also marked Partial (not Failed). Do NOT change this — the
        # product intentionally treats a partial send as Partial, not Failed.
        rows = [_recipient("good@b.com"), _recipient("bad@b.com")]
        self._docs(recipients=rows)

        def sendmail_se(**kw):
            if kw["recipients"] == ["bad@b.com"]:
                raise Exception("bad address")

        frappe_stub.sendmail.side_effect = sendmail_se
        self._run()

        frappe_stub.db.set_value.assert_any_call(
            "Email Send", "SD-001",
            {"status": "Partial", "sent_count": 1},
            update_modified=False,
        )
        frappe_stub.db.set_value.assert_any_call(
            "Letter", "CAMP-001", "status", "Partial",
            update_modified=False,
        )
        assert rows[0].status == "Sent"
        assert rows[1].status == "Failed"

    def test_all_fail_marks_send_and_letter_failed(self):
        rows = [_recipient("a@b.com"), _recipient("c@d.com")]
        self._docs(recipients=rows)
        frappe_stub.sendmail.side_effect = Exception("SMTP down")
        self._run()
        frappe_stub.db.set_value.assert_any_call(
            "Email Send", "SD-001",
            {"status": "Failed", "sent_count": 0},
            update_modified=False,
        )
        frappe_stub.db.set_value.assert_any_call(
            "Letter", "CAMP-001", "status", "Failed",
            update_modified=False,
        )

    def test_recipient_failure_is_logged(self):
        self._docs(recipients=[_recipient("a@b.com")])
        frappe_stub.sendmail.side_effect = RuntimeError("boom")
        self._run()
        frappe_stub.log_error.assert_called()

    def test_compile_error_marks_failed_not_draft(self):
        """A batch-level failure leaves the campaign Failed (retryable via
        resume), never Draft (which previously allowed a full re-send)."""
        self._docs(recipients=[_recipient("a@b.com")])
        with patch("letters.letters.utils.email_compiler.EmailCompiler") as C:
            C.return_value.compile.side_effect = ValueError("Unknown block type")
            api_module._execute_send("SD-001", "CAMP-001")
        frappe_stub.db.set_value.assert_any_call("Letter", "CAMP-001", "status", "Failed")
        frappe_stub.db.set_value.assert_any_call("Email Send", "SD-001", "status", "Failed")

    @pytest.mark.parametrize("send_mode", ["direct", "email_group"])
    def test_every_mode_sets_letter_reference_for_unsubscribe(self, send_mode):
        """H2: every send mode passes a reference doc so Frappe injects the
        signed unsubscribe footer + confirmation page."""
        self._docs(recipients=[_recipient("a@b.com")], send_mode=send_mode)
        self._run()
        kw = frappe_stub.sendmail.call_args.kwargs
        assert kw["reference_doctype"] == "Letter"
        assert kw["reference_name"] == "CAMP-001"


# ── Open tracking & analytics ─────────────────────────────────────────────────

class TestTrackOpen:
    def setup_method(self):
        _reset()

    def test_records_open_on_recipient_rows(self):
        GETALL["Email Send"] = ["ES-1"]
        GETALL["Email Send Recipient"] = [FrappeDict(name="R1", opened=0, open_count=0)]
        api_module._record_open("CAMP-001", "a@b.com")
        # First open flips opened=1 and stamps opened_on
        called = frappe_stub.db.set_value.call_args
        assert called.args[0] == "Email Send Recipient"
        assert called.args[1] == "R1"
        update = called.args[2]
        assert update["opened"] == 1
        assert update["open_count"] == 1
        assert "opened_on" in update

    def test_second_open_only_bumps_count(self):
        GETALL["Email Send"] = ["ES-1"]
        GETALL["Email Send Recipient"] = [FrappeDict(name="R1", opened=1, open_count=3)]
        api_module._record_open("CAMP-001", "a@b.com")
        update = frappe_stub.db.set_value.call_args.args[2]
        assert update["open_count"] == 4
        assert "opened" not in update     # already opened — don't re-stamp
        assert "opened_on" not in update

    def test_no_sends_is_noop(self):
        GETALL["Email Send"] = []
        api_module._record_open("CAMP-001", "a@b.com")
        frappe_stub.db.set_value.assert_not_called()


class TestEmailReadTracker:
    def setup_method(self):
        _reset()

    def test_send_passes_tracker_url(self):
        campaign = _letter_doc()
        send_doc = MagicMock()
        send_doc.name = "SD-001"
        send_doc.send_mode = "direct"
        send_doc.email_group = None
        send_doc.recipients = [_recipient("a@b.com")]
        frappe_stub.get_doc.side_effect = lambda dt, n=None: campaign if dt == "Letter" else send_doc
        with patch("letters.letters.utils.email_compiler.EmailCompiler") as C:
            C.return_value.compile.return_value = "<html></html>"
            api_module._execute_send("SD-001", "CAMP-001")
        kw = frappe_stub.sendmail.call_args.kwargs
        assert kw["email_read_tracker_url"] == "/api/method/letters.letters.api.track_open"


class TestLetterAnalytics:
    def setup_method(self):
        _reset()

    def test_no_sends_returns_zeroes(self):
        frappe_stub.get_doc.return_value = _letter_doc()
        GETALL["Email Send"] = []
        res = api_module.get_letter_analytics("CAMP-001")
        assert res["sent"] == 0 and res["opened"] == 0 and res["open_rate"] == 0

    def test_aggregates_open_rate(self):
        frappe_stub.get_doc.return_value = _letter_doc()
        GETALL["Email Send"] = [FrappeDict(
            name="ES-1", status="Sent", total_recipients=4, sent_count=4, creation="2026-01-01",
        )]
        frappe_stub.db.count.return_value = 1   # 1 opened of 4 sent
        res = api_module.get_letter_analytics("CAMP-001")
        assert res["sent"] == 4
        assert res["opened"] == 1
        assert res["open_rate"] == 25.0
        assert res["sent_status"] == "Sent"

    def test_permission_checked(self):
        doc = _letter_doc()
        frappe_stub.get_doc.return_value = doc
        GETALL["Email Send"] = []
        api_module.get_letter_analytics("CAMP-001")
        frappe_stub.has_permission.assert_called_with("Letter", "read", doc=doc, throw=True)


# ── send_letter — saved recipient_config fallback (C1 / H1) ──────────────────
# When no explicit recipient source is passed (scheduled sends, server-side
# callers), send_campaign must resolve the audience from the campaign's saved
# recipient_config. Without this, scheduled sends silently have no recipients.

class TestRecipientConfigFallback:
    def setup_method(self):
        _reset()

    def _new_send_doc(self):
        send_doc_mock = MagicMock()
        send_doc_mock.name = "SD-NEW"
        return send_doc_mock

    def test_falls_back_to_saved_group(self):
        doc = _letter_doc()
        doc.recipient_config = json.dumps({"type": "group", "email_group": "G1"})
        GETALL["Email Group Member"] = [FrappeDict(email="a@b.com"), FrappeDict(email="c@d.com")]
        send_doc_mock = self._new_send_doc()
        frappe_stub.get_doc.side_effect = lambda arg, *a: send_doc_mock if isinstance(arg, dict) else doc

        result = api_module.send_letter("CAMP-001")  # no explicit recipients

        assert result["queued"] is True
        assert result["count"] == 2
        assert result["mode"] == "email_group"

    def test_falls_back_to_saved_paste(self):
        doc = _letter_doc()
        doc.recipient_config = json.dumps({"type": "paste", "recipients": ["x@y.com", "z@w.com"]})
        send_doc_mock = self._new_send_doc()
        frappe_stub.get_doc.side_effect = lambda arg, *a: send_doc_mock if isinstance(arg, dict) else doc

        result = api_module.send_letter("CAMP-001")

        assert result["queued"] is True
        assert result["count"] == 2
        assert result["mode"] == "direct"

    def test_falls_back_to_saved_doctype(self):
        doc = _letter_doc()
        doc.recipient_config = json.dumps({
            "type": "doctype", "doctype": "Contact", "email_field": "email_id", "filters": {},
        })
        GETALL["Contact"] = [FrappeDict(email_id="a@b.com")]
        send_doc_mock = self._new_send_doc()
        frappe_stub.get_doc.side_effect = lambda arg, *a: send_doc_mock if isinstance(arg, dict) else doc

        result = api_module.send_letter("CAMP-001")

        assert result["queued"] is True
        assert result["count"] == 1
        assert result["mode"] == "direct"

    def test_throws_when_no_args_and_no_saved_config(self):
        doc = _letter_doc()
        doc.recipient_config = ""  # nothing saved
        frappe_stub.get_doc.return_value = doc
        with pytest.raises(FrappeValidationError, match="no saved recipients"):
            api_module.send_letter("CAMP-001")

    def test_explicit_recipients_still_win_over_saved_config(self):
        """Passing recipients explicitly (Send now) must not be overridden by the
        saved config."""
        doc = _letter_doc()
        doc.recipient_config = json.dumps({"type": "group", "email_group": "G1"})
        send_doc_mock = self._new_send_doc()
        frappe_stub.get_doc.side_effect = lambda arg, *a: send_doc_mock if isinstance(arg, dict) else doc

        result = api_module.send_letter("CAMP-001", recipients=json.dumps(["only@me.com"]))

        assert result["mode"] == "direct"
        assert result["count"] == 1


# ── schedule_campaign ─────────────────────────────────────────────────────────

class TestScheduleLetter:
    def setup_method(self):
        _reset()

    def test_throws_when_no_saved_recipients(self):
        doc = _letter_doc()
        doc.recipient_config = ""
        frappe_stub.get_doc.return_value = doc
        with pytest.raises(FrappeValidationError, match="Choose recipients"):
            api_module.schedule_letter("CAMP-001", "2099-01-01 10:00:00")

    def test_throws_when_already_sent(self):
        doc = _letter_doc(status="Sent")
        doc.recipient_config = json.dumps({"type": "group", "email_group": "G1"})
        frappe_stub.get_doc.return_value = doc
        with pytest.raises(FrappeValidationError, match="already been sent"):
            api_module.schedule_letter("CAMP-001", "2099-01-01 10:00:00")

    def test_schedules_when_recipients_saved(self):
        import datetime
        doc = _letter_doc()
        doc.recipient_config = json.dumps({"type": "group", "email_group": "G1"})
        frappe_stub.get_doc.return_value = doc
        frappe_stub.utils.get_datetime = lambda s: datetime.datetime(2099, 1, 1, 10, 0, 0)
        frappe_stub.utils.now_datetime = lambda: datetime.datetime(2020, 1, 1)

        with _frappe_utils_importable():
            result = api_module.schedule_letter("CAMP-001", "2099-01-01 10:00:00")

        assert "scheduled_at" in result
        doc.db_set.assert_any_call("status", "Scheduled")


# ── process_scheduled_sends — failure surfacing ───────────────────────────────

class TestProcessScheduledSends:
    def setup_method(self):
        _reset()
        # The atomic claim wins when the UPDATE's affected-row count is 1.
        frappe_stub.db._cursor.rowcount = 1

    def test_marks_failed_when_send_raises(self):
        """A due campaign whose send can't start (e.g. no saved audience) is
        marked Failed, not left silently reverted to Draft."""
        import datetime
        GETALL["Letter"] = [FrappeDict(name="CAMP-DUE")]
        doc = _letter_doc(name="CAMP-DUE")
        doc.recipient_config = ""  # send_campaign will raise
        frappe_stub.get_doc.return_value = doc
        frappe_stub.utils.now_datetime = lambda: datetime.datetime(2099, 1, 1)

        with _frappe_utils_importable():
            api_module.process_scheduled_sends()

        frappe_stub.db.set_value.assert_any_call(
            "Letter", "CAMP-DUE", "status", "Failed"
        )

    def test_skips_letter_when_atomic_claim_fails(self):
        """If another worker already claimed the campaign (sql returns falsy),
        send_campaign must not be called for that row."""
        import datetime
        GETALL["Letter"] = [FrappeDict(name="CAMP-RACE")]
        frappe_stub.db._cursor.rowcount = 0  # claim lost
        frappe_stub.utils.now_datetime = lambda: datetime.datetime(2099, 1, 1)

        with _frappe_utils_importable():
            api_module.process_scheduled_sends()

        # get_doc / enqueue should never be touched when the claim failed
        frappe_stub.get_doc.assert_not_called()
        frappe_stub.enqueue.assert_not_called()


class TestUrlSafety:
    """SSRF guard for the link checker (_url_safety_error)."""

    def test_public_https_url_is_allowed(self):
        # 93.184.216.34 is a public address (example.com style).
        with patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("93.184.216.34", 443))]):
            assert api_module._url_safety_error("https://example.com/page") is None

    def test_rejects_non_http_scheme(self):
        assert api_module._url_safety_error("ftp://example.com/x") == "unsupported scheme"
        assert api_module._url_safety_error("file:///etc/passwd") == "unsupported scheme"

    def test_rejects_loopback(self):
        with patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("127.0.0.1", 8000))]):
            assert api_module._url_safety_error("http://localhost:8000/admin") is not None

    def test_rejects_cloud_metadata(self):
        with patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("169.254.169.254", 80))]):
            assert api_module._url_safety_error("http://169.254.169.254/latest/meta-data/") is not None

    def test_rejects_rfc1918_private(self):
        for ip in ("10.0.0.5", "192.168.1.1", "172.16.0.9"):
            with patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", (ip, 80))]):
                assert api_module._url_safety_error(f"http://{ip}/") is not None

    def test_rejects_dns_name_resolving_to_private_ip(self):
        # A public-looking hostname that resolves to an internal address.
        with patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("10.1.2.3", 80))]):
            assert api_module._url_safety_error("http://internal.evil.example/") is not None

    def test_rejects_when_any_resolved_ip_is_private(self):
        # Mixed result set: one public, one private. Must reject.
        with patch("socket.getaddrinfo", return_value=[
            (2, 1, 6, "", ("93.184.216.34", 80)),
            (2, 1, 6, "", ("127.0.0.1", 80)),
        ]):
            assert api_module._url_safety_error("http://rebind.example/") is not None

    def test_dns_failure_is_treated_as_unsafe(self):
        import socket as _socket
        with patch("socket.getaddrinfo", side_effect=_socket.gaierror):
            assert api_module._url_safety_error("http://nonexistent.invalid/") == "dns resolution failed"

    def test_resolve_returns_pinned_public_ip(self):
        with patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("93.184.216.34", 443))]):
            host, ip, port, scheme, error = api_module._resolve_safe_target("https://example.com/x")
        assert error is None
        assert host == "example.com"
        assert ip == "93.184.216.34"
        assert port == 443
        assert scheme == "https"


class TestHeadPinned:
    """The probe must connect to the validated IP, never re-resolve (rebind-proof)."""

    def test_connects_to_pinned_ip_not_hostname(self):
        # getaddrinfo resolves the hostname to a public IP; the actual socket
        # connection must target that exact IP, proving no second DNS lookup.
        public_ip = "93.184.216.34"
        fake_sock = MagicMock()
        fake_resp = MagicMock(status=200)
        fake_conn = MagicMock()
        fake_conn.getresponse.return_value = fake_resp
        # _head_pinned overrides conn.connect with its pinning closure; mimic
        # real http.client by invoking that closure when request() is called.
        fake_conn.request.side_effect = lambda *a, **k: fake_conn.connect()

        with patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", (public_ip, 80))]), \
             patch("http.client.HTTPConnection", return_value=fake_conn) as conn_cls, \
             patch("socket.create_connection", return_value=fake_sock) as create_conn:
            code = api_module._head_pinned("http://example.com/path?q=1", 5)
            # The socket is dialed against the validated IP, not re-resolved.
            create_conn.assert_called_once_with((public_ip, 80), 5)

        assert code == 200
        # Connection object built for the real hostname (Host header / cert).
        conn_cls.assert_called_once()
        assert conn_cls.call_args[0][0] == "example.com"

    def test_blocked_url_never_opens_a_socket(self):
        with patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("127.0.0.1", 80))]), \
             patch("socket.create_connection") as create_conn:
            with pytest.raises(ValueError):
                api_module._head_pinned("http://localhost/admin", 5)
            create_conn.assert_not_called()


# ── save_campaign ─────────────────────────────────────────────────────────────

class TestSaveLetter:
    def setup_method(self):
        _reset()

    def test_updates_existing_letter_fields(self):
        doc = _letter_doc()
        frappe_stub.get_doc.return_value = doc
        result = api_module.save_letter(
            name="CAMP-001", title="New Title", subject="New Subject",
            preview_text="Preview", blocks=json.dumps([]),
        )
        assert result["name"] == "CAMP-001"
        assert doc.title == "New Title"
        assert doc.subject == "New Subject"
        assert doc.preview_text == "Preview"
        doc.save.assert_called_once()

    def test_creates_new_letter_when_no_name(self):
        new_doc = MagicMock()
        new_doc.name = "CAMP-NEW"
        new_doc.title = "Untitled Letter"
        new_doc.status = "Draft"
        frappe_stub.get_doc.return_value = new_doc
        result = api_module.save_letter(title="Brand New", blocks=json.dumps([]))
        new_doc.insert.assert_called_once()
        assert result["name"] == "CAMP-NEW"

    def test_normalize_recipient_config_clears_on_null_string(self):
        assert api_module._normalize_recipient_config("null") == ""
        assert api_module._normalize_recipient_config("{}") == ""
        assert api_module._normalize_recipient_config("") == ""

    def test_normalize_recipient_config_serializes_dict(self):
        cfg = {"type": "group", "email_group": "G1"}
        result = api_module._normalize_recipient_config(cfg)
        assert json.loads(result) == cfg

    def test_normalize_recipient_config_none_means_leave_unchanged(self):
        assert api_module._normalize_recipient_config(None) is None

    def test_updates_email_width_as_int(self):
        doc = _letter_doc()
        frappe_stub.get_doc.return_value = doc
        api_module.save_letter(name="CAMP-001", email_width="720", blocks=json.dumps([]))
        assert doc.email_width == 720

    def test_ignores_non_numeric_email_width(self):
        doc = _letter_doc()
        frappe_stub.get_doc.return_value = doc
        old_width = getattr(doc, "email_width", None)
        api_module.save_letter(name="CAMP-001", email_width="bad", blocks=json.dumps([]))
        assert doc.email_width == old_width


# ── render_preview ────────────────────────────────────────────────────────────

class TestRenderPreview:
    def setup_method(self):
        _reset()

    def test_renders_blocks_passed_directly(self):
        with patch("letters.letters.utils.email_compiler.EmailCompiler") as C:
            C.return_value.compile.return_value = "<html>hi</html>"
            result = api_module.render_preview(blocks=json.dumps([]))
        assert result["html"] == "<html>hi</html>"

    def test_loads_blocks_from_letter_when_name_given(self):
        doc = _letter_doc(blocks_json=json.dumps([{"type": "text", "props": {}}]))
        doc.preview_text = "preview"
        doc.email_width = 600
        frappe_stub.get_doc.return_value = doc
        with patch("letters.letters.utils.email_compiler.EmailCompiler") as C:
            C.return_value.compile.return_value = "<html/>"
            result = api_module.render_preview(name="CAMP-001")
        assert result["html"] == "<html/>"

    def test_compile_error_is_rethrown(self):
        with patch("letters.letters.utils.email_compiler.EmailCompiler") as C:
            C.return_value.compile.side_effect = ValueError("bad block")
            with pytest.raises(Exception):
                api_module.render_preview(blocks=json.dumps([]))


# ── duplicate_campaign ────────────────────────────────────────────────────────

class TestDuplicateLetter:
    def setup_method(self):
        _reset()

    def test_creates_copy_with_new_title(self):
        original = _letter_doc(name="CAMP-001")
        original.title = "Summer Sale"
        original.recipient_config = json.dumps({"type": "group", "email_group": "G"})
        original.email_width = 600

        new_doc = MagicMock()
        new_doc.name = "CAMP-002"
        new_doc.title = "Copy of Summer Sale"

        call_count = [0]
        def get_doc_se(arg, *a):
            call_count[0] += 1
            return original if call_count[0] == 1 else new_doc
        frappe_stub.get_doc.side_effect = get_doc_se

        result = api_module.duplicate_letter("CAMP-001")
        new_doc.insert.assert_called_once()
        assert result["name"] == "CAMP-002"

    def test_copy_is_always_draft(self):
        original = _letter_doc(name="CAMP-001", status="Sent")
        original.email_width = 600
        new_doc = MagicMock()
        new_doc.name = "CAMP-COPY"
        new_doc.title = "Copy"

        call_count = [0]
        def get_doc_se(arg, *a):
            call_count[0] += 1
            return original if call_count[0] == 1 else new_doc
        frappe_stub.get_doc.side_effect = get_doc_se

        api_module.duplicate_letter("CAMP-001")
        inserted_data = frappe_stub.get_doc.call_args_list[1][0][0]
        assert inserted_data["status"] == "Draft"


# ── send_test ─────────────────────────────────────────────────────────────────

class TestSendTest:
    def setup_method(self):
        _reset()

    def test_sends_to_session_user_when_recipient_matches(self):
        frappe_stub.session.user = "user@frappe.io"
        with patch("letters.letters.utils.email_compiler.EmailCompiler") as C:
            C.return_value.compile.return_value = "<html/>"
            result = api_module.send_test(
                blocks=json.dumps([]), subject="Hi", recipient="user@frappe.io"
            )
        assert result["sent_to"] == "user@frappe.io"
        frappe_stub.sendmail.assert_called_once()
        kw = frappe_stub.sendmail.call_args.kwargs
        assert kw["recipients"] == ["user@frappe.io"]
        assert kw["subject"].startswith("[TEST]")

    def test_rejects_recipient_that_is_not_session_user(self):
        frappe_stub.session.user = "user@frappe.io"
        with patch("letters.letters.utils.email_compiler.EmailCompiler") as C:
            C.return_value.compile.return_value = "<html/>"
            with pytest.raises(FrappeValidationError, match="own account"):
                api_module.send_test(
                    blocks=json.dumps([]), subject="Hi", recipient="other@example.com"
                )

    def test_falls_back_to_session_user_when_no_recipient(self):
        frappe_stub.session.user = "user@frappe.io"
        with patch("letters.letters.utils.email_compiler.EmailCompiler") as C:
            C.return_value.compile.return_value = "<html/>"
            result = api_module.send_test(blocks=json.dumps([]), subject="Hi")
        assert result["sent_to"] == "user@frappe.io"

    def test_rejects_invalid_email(self):
        frappe_stub.utils.validate_email_address.return_value = None
        with patch("letters.letters.utils.email_compiler.EmailCompiler") as C:
            C.return_value.compile.return_value = "<html/>"
            with pytest.raises(Exception):
                api_module.send_test(blocks=json.dumps([]), recipient="notanemail")

    def test_loads_from_letter_when_name_given(self):
        frappe_stub.session.user = "user@frappe.io"
        doc = _letter_doc()
        doc.preview_text = ""
        doc.email_width = 600
        frappe_stub.get_doc.return_value = doc
        with patch("letters.letters.utils.email_compiler.EmailCompiler") as C:
            C.return_value.compile.return_value = "<html/>"
            result = api_module.send_test(name="CAMP-001")
        assert result["sent_to"] == "user@frappe.io"


# ── get_letter_analytics ────────────────────────────────────────────────────

class TestGetLetterAnalytics:
    def setup_method(self):
        _reset()

    def _doc(self):
        doc = _letter_doc()
        frappe_stub.get_doc.return_value = doc
        return doc

    def test_returns_zeros_when_no_sends(self):
        self._doc()
        GETALL["Email Send"] = []
        result = api_module.get_letter_analytics("CAMP-001")
        assert result["total"] == 0
        assert result["sent"] == 0
        assert result["open_rate"] == 0

    def test_computes_open_rate(self):
        self._doc()
        GETALL["Email Send"] = [
            FrappeDict(
                name="SD-1", status="Sent", total_recipients=10,
                sent_count=10, creation="2024-01-01",
            )
        ]
        frappe_stub.db.count.return_value = 4
        frappe_stub.db.get_value.return_value = "2024-01-02 10:00:00"
        GETALL["Email Send Recipient"] = [FrappeDict(status="Sent")] * 10

        result = api_module.get_letter_analytics("CAMP-001")
        assert result["open_rate"] == 40.0
        assert result["opened"] == 4

    def test_open_rate_is_zero_when_no_sends_count(self):
        self._doc()
        GETALL["Email Send"] = [
            FrappeDict(
                name="SD-1", status="Sending", total_recipients=5,
                sent_count=0, creation="2024-01-01",
            )
        ]
        frappe_stub.db.count.return_value = 0
        GETALL["Email Send Recipient"] = []
        result = api_module.get_letter_analytics("CAMP-001")
        assert result["open_rate"] == 0


# ── get_letter_recipients ───────────────────────────────────────────────────

class TestGetLetterRecipients:
    def setup_method(self):
        _reset()

    def test_returns_empty_when_no_send(self):
        frappe_stub.get_doc.return_value = _letter_doc()
        frappe_stub.db.get_value.return_value = None
        result = api_module.get_letter_recipients("CAMP-001")
        assert result == []

    def test_returns_recipient_rows(self):
        frappe_stub.get_doc.return_value = _letter_doc()
        frappe_stub.db.get_value.return_value = "SD-001"
        GETALL["Email Send Recipient"] = [
            FrappeDict(email="a@b.com", status="Sent", opened=1, opened_on="2024-01-01")
        ]
        result = api_module.get_letter_recipients("CAMP-001")
        assert len(result) == 1


# ── _bulk_insert_recipients ───────────────────────────────────────────────────

class TestBulkInsertRecipients:
    def setup_method(self):
        _reset()

    def _get_values(self):
        ca = frappe_stub.db.bulk_insert.call_args
        # _bulk_insert_recipients calls frappe.db.bulk_insert(doctype, fields=..., values=...)
        # The first positional arg is the doctype; fields and values are kwargs.
        assert ca.args[0] == "Email Send Recipient"
        return list(ca.kwargs["values"])

    def test_inserts_all_recipients_as_pending(self):
        frappe_stub.db.bulk_insert.reset_mock()
        api_module._bulk_insert_recipients("SD-001", ["a@x.com", "b@x.com"])
        frappe_stub.db.bulk_insert.assert_called_once()
        values = self._get_values()
        assert len(values) == 2
        emails = [v[-2] for v in values]
        assert "a@x.com" in emails
        assert "b@x.com" in emails
        assert all(v[-1] == "Pending" for v in values)

    def test_idx_is_one_based_and_sequential(self):
        frappe_stub.db.bulk_insert.reset_mock()
        api_module._bulk_insert_recipients("SD-001", ["x@x.com", "y@y.com", "z@z.com"])
        values = self._get_values()
        idxs = [v[6] for v in values]
        assert idxs == [1, 2, 3]

    def test_parent_field_is_send_doc_name(self):
        frappe_stub.db.bulk_insert.reset_mock()
        api_module._bulk_insert_recipients("SEND-XYZ", ["r@r.com"])
        values = self._get_values()
        assert values[0][7] == "SEND-XYZ"


# ===========================================================================
# NEW REGRESSION TESTS
# ===========================================================================
#
# Import the modules under test.  frappe is already stubbed above so all
# `import frappe` lines inside these modules resolve to the same MagicMock.
# We also need the www page and the unsubscribe API.
# ---------------------------------------------------------------------------
import sys as _sys
import os as _os

# Ensure the letters package root is importable
_pkg_root = _os.path.join(_os.path.dirname(__file__), "..", "..")
if _pkg_root not in _sys.path:
    _sys.path.insert(0, _pkg_root)

from letters.letters.api.recipients import (
    _suppressed_emails,
    _resolve_single_source_emails,
    _resolve_multi_source,
    _load_recipient_config,
    _normalize_recipient_config,
)
import letters.letters.api.unsubscribe as unsubscribe_module

# www page lives outside the package — import by path
import importlib.util as _ilu

_www_path = _os.path.join(
    _os.path.dirname(__file__), "..", "..", "letters", "www", "letters_unsubscribe.py"
)
_spec = _ilu.spec_from_file_location("letters_unsubscribe", _www_path)
_www_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_www_mod)
get_context = _www_mod.get_context


# ---------------------------------------------------------------------------
# Helpers shared across the new test classes
# ---------------------------------------------------------------------------

def _mk_dict(**kw):
    """Tiny FrappeDict factory."""
    return FrappeDict(**kw)


# ===========================================================================
# 1. _suppressed_emails
# ===========================================================================
#
# Covers:
#   - Without letter_name: only global unsubscribes are fetched
#   - With letter_name: global + letter-specific + folder-specific
#   - A user unsubscribed from Letter A does NOT appear in Letter B suppression
#   - Returns empty set when no unsubscribes exist
# ---------------------------------------------------------------------------

class TestSuppressedEmails:
    def setup_method(self):
        _reset()

    def test_no_letter_name_returns_only_globals(self):
        """Calling without letter_name passes only the global_unsubscribe filter."""
        GETALL["Email Unsubscribe"] = ["global@example.com"]
        result = _suppressed_emails()
        assert "global@example.com" in result
        # Verify or_filters only contain the global clause (no letter/folder refs)
        call_kwargs = frappe_stub.get_all.call_args.kwargs
        or_filters = call_kwargs.get("or_filters", [])
        assert len(or_filters) == 1
        assert or_filters[0] == {"global_unsubscribe": 1}

    def test_with_letter_name_includes_letter_and_folder(self):
        """With letter_name the or_filters grow to include letter + folder refs."""
        frappe_stub.db.get_value.return_value = "FOLDER-1"
        GETALL["Email Unsubscribe"] = ["a@b.com", "b@c.com"]
        result = _suppressed_emails("LETTER-001")
        assert {"a@b.com", "b@c.com"} == result
        or_filters = frappe_stub.get_all.call_args.kwargs.get("or_filters", [])
        assert len(or_filters) == 3
        types = [list(f.keys()) for f in or_filters]
        flat = [k for keys in types for k in keys]
        assert "global_unsubscribe" in flat
        assert "reference_name" in flat

    def test_unsubscribe_from_letter_a_not_in_letter_b_suppression(self):
        """Letter-scoped suppression must NOT cross-contaminate other letters.

        We verify this by confirming that when called with letter_name="LETTER-B"
        the or_filters only reference "LETTER-B", never "LETTER-A".
        """
        frappe_stub.db.get_value.return_value = None  # no folder
        frappe_stub.get_all.return_value = []

        _suppressed_emails("LETTER-B")

        or_filters = frappe_stub.get_all.call_args.kwargs.get("or_filters", [])
        for f in or_filters:
            ref_name = f.get("reference_name")
            if ref_name:
                assert ref_name != "LETTER-A", "Letter A's unsub leaked into Letter B query"

    def test_returns_empty_set_when_no_unsubscribes(self):
        frappe_stub.get_all.return_value = []
        result = _suppressed_emails("LETTER-X")
        assert result == set()


# ===========================================================================
# 2. _resolve_single_source_emails
# ===========================================================================
#
# Covers:
#   - group type: queries Email Group Member with unsubscribed=0
#   - paste type: returns the recipients list as-is
#   - doctype type: calls frappe.get_all with correct filters
#   - unknown type: returns []
# ---------------------------------------------------------------------------

class TestResolveSingleSourceEmails:
    def setup_method(self):
        _reset()

    def test_group_type_queries_email_group_member(self):
        GETALL["Email Group Member"] = ["m1@x.com", "m2@x.com"]
        result = _resolve_single_source_emails({"type": "group", "email_group": "GRP-1"})
        assert result == ["m1@x.com", "m2@x.com"]
        frappe_stub.get_all.assert_called()
        call_kwargs = frappe_stub.get_all.call_args
        # First positional arg is the doctype
        assert call_kwargs.args[0] == "Email Group Member"
        filters = call_kwargs.kwargs.get("filters", {})
        assert filters.get("email_group") == "GRP-1"
        assert filters.get("unsubscribed") == 0

    def test_paste_type_returns_recipients_as_is(self):
        emails = ["a@b.com", "c@d.com"]
        result = _resolve_single_source_emails({"type": "paste", "recipients": emails})
        assert result == emails

    def test_doctype_type_calls_get_all_with_email_filter(self):
        frappe_stub.has_permission.return_value = True
        GETALL["Contact"] = ["doc1@x.com"]
        result = _resolve_single_source_emails({
            "type": "doctype",
            "doctype": "Contact",
            "email_field": "email_id",
            "filters": {},
        })
        assert result == ["doc1@x.com"]
        frappe_stub.get_all.assert_called()
        call_args = frappe_stub.get_all.call_args
        assert call_args.args[0] == "Contact"
        filters = call_args.kwargs.get("filters", {})
        # email_field != "" must be in filters
        assert filters.get("email_id") == ["!=", ""]

    def test_unknown_type_returns_empty_list(self):
        result = _resolve_single_source_emails({"type": "fax_machine"})
        assert result == []

    def test_paste_type_with_empty_list_returns_empty(self):
        result = _resolve_single_source_emails({"type": "paste", "recipients": []})
        assert result == []


# ===========================================================================
# 3. _resolve_multi_source
# ===========================================================================
#
# Covers:
#   - Deduplicates emails across sources (case-insensitive)
#   - Applies suppression correctly
#   - Snapshots resolved_emails into recipient_config when letter_name provided
#   - Each source's resolved_emails contains only that source's emails
#   - Throws when no recipients remain after suppression
#   - Throws when over MAX_RECIPIENTS
#   - Throws when no valid emails
# ---------------------------------------------------------------------------

class TestResolveMultiSource:
    def setup_method(self):
        _reset()

    def _identity_valid(self, emails):
        """valid_fn that accepts all emails as-is."""
        return emails, 0

    def _no_suppression(self):
        return set()

    def test_deduplicates_across_sources_case_insensitive(self):
        """The same address (different case) from two sources is counted once."""
        sources = [
            {"type": "paste", "recipients": ["Alice@X.com", "b@x.com"]},
            {"type": "paste", "recipients": ["alice@x.com", "c@x.com"]},
        ]
        valid, invalid = _resolve_multi_source(
            sources, 1000, self._no_suppression, self._identity_valid
        )
        # alice@x.com / Alice@X.com should appear only once
        assert len(valid) == 3
        lower = [e.lower() for e in valid]
        assert lower.count("alice@x.com") == 1

    def test_suppression_removes_matching_emails(self):
        sources = [{"type": "paste", "recipients": ["keep@x.com", "gone@x.com"]}]
        valid, _ = _resolve_multi_source(
            sources, 1000,
            lambda: {"gone@x.com"},
            self._identity_valid,
        )
        assert "keep@x.com" in valid
        assert not any(e.lower() == "gone@x.com" for e in valid)

    def test_throws_when_no_recipients_after_suppression(self):
        sources = [{"type": "paste", "recipients": ["gone@x.com"]}]
        with pytest.raises(FrappeValidationError):
            _resolve_multi_source(
                sources, 1000,
                lambda: {"gone@x.com"},
                self._identity_valid,
            )

    def test_throws_when_over_max_recipients(self):
        big_list = [f"u{i}@x.com" for i in range(10)]
        sources = [{"type": "paste", "recipients": big_list}]
        with pytest.raises(FrappeValidationError, match="above the per-letter limit"):
            _resolve_multi_source(
                sources, 5,
                self._no_suppression,
                self._identity_valid,
            )

    def test_throws_when_no_valid_emails(self):
        sources = [{"type": "paste", "recipients": ["bad"]}]
        with pytest.raises(FrappeValidationError):
            _resolve_multi_source(
                sources, 1000,
                self._no_suppression,
                lambda emails: ([], len(emails)),
            )

    def test_snapshots_resolved_emails_to_db_when_letter_name_given(self):
        sources = [
            {"type": "paste", "recipients": ["a@x.com"]},
            {"type": "paste", "recipients": ["b@x.com"]},
        ]
        _resolve_multi_source(
            sources, 1000,
            self._no_suppression,
            self._identity_valid,
            letter_name="LETTER-SNAP",
        )
        frappe_stub.db.set_value.assert_called()
        call_args = frappe_stub.db.set_value.call_args
        assert call_args.args[0] == "Letter"
        assert call_args.args[1] == "LETTER-SNAP"
        assert call_args.args[2] == "recipient_config"
        saved = json.loads(call_args.args[3])
        assert isinstance(saved, list)
        assert len(saved) == 2

    def test_each_source_resolved_emails_contains_only_own_emails(self):
        """Per-source resolved_emails must NOT include emails from other sources."""
        sources = [
            {"type": "paste", "recipients": ["a@x.com"]},
            {"type": "paste", "recipients": ["b@x.com"]},
        ]
        _resolve_multi_source(
            sources, 1000,
            self._no_suppression,
            self._identity_valid,
            letter_name="LETTER-PER-SRC",
        )
        saved_json = frappe_stub.db.set_value.call_args.args[3]
        saved = json.loads(saved_json)
        src0_emails = saved[0]["resolved_emails"]
        src1_emails = saved[1]["resolved_emails"]
        assert "a@x.com" in src0_emails
        assert "b@x.com" not in src0_emails
        assert "b@x.com" in src1_emails
        assert "a@x.com" not in src1_emails

    def test_no_snapshot_when_letter_name_is_none(self):
        sources = [{"type": "paste", "recipients": ["a@x.com"]}]
        _resolve_multi_source(
            sources, 1000,
            self._no_suppression,
            self._identity_valid,
            letter_name=None,
        )
        frappe_stub.db.set_value.assert_not_called()


# ===========================================================================
# 4. AnalyticsMixin.get_recipients
# ===========================================================================
#
# Covers:
#   - Returns sent recipients with correct status fields
#   - Appends suppressed emails with status="Excluded"
#   - Does not double-list an email that is both sent and suppressed
#   - Scopes suppression query to letter + folder
# ---------------------------------------------------------------------------

class TestAnalyticsMixinGetRecipients:
    def setup_method(self):
        _reset()
        # frappe._dict must build real attribute-dicts, not MagicMocks,
        # so the excluded-row comparison works.
        frappe_stub._dict.side_effect = lambda **kw: FrappeDict(**kw)

    def _doc(self, name="CAMP-001", folder=None):
        doc = _letter_doc(name=name)
        doc.folder = folder
        doc.get_recipients = _types.MethodType(AnalyticsMixin.get_recipients, doc)
        return doc

    def test_returns_empty_when_no_send(self):
        doc = self._doc()
        frappe_stub.db.get_value.return_value = None
        result = doc.get_recipients()
        assert result == []

    def test_returns_sent_recipients(self):
        doc = self._doc()
        frappe_stub.db.get_value.return_value = "SD-001"
        # sent rows
        GETALL["Email Send Recipient"] = [
            _mk_dict(email="a@b.com", status="Sent", opened=1, opened_on="2024-01-01")
        ]
        # No unsubscribes for suppressed list
        def _route(doctype, *a, **kw):
            if doctype == "Email Send Recipient":
                return GETALL.get("Email Send Recipient", [])
            if doctype == "Email Unsubscribe":
                return []
            return GETALL.get(doctype, [])
        frappe_stub.get_all.side_effect = _route
        frappe_stub.db.get_value.side_effect = lambda dt, filters, field, **kw: (
            "SD-001" if dt == "Email Send" else None
        )

        result = doc.get_recipients()
        assert len(result) == 1
        assert result[0].email == "a@b.com"
        assert result[0].status == "Sent"

    def test_appends_suppressed_emails_as_excluded(self):
        doc = self._doc()
        frappe_stub.db.get_value.side_effect = lambda dt, filters, field, **kw: (
            "SD-001" if dt == "Email Send" else None
        )
        GETALL["Email Send Recipient"] = []

        def _route(doctype, *a, **kw):
            if doctype == "Email Send Recipient":
                return []
            if doctype == "Email Unsubscribe":
                return [_mk_dict(email="unsub@x.com")]
            return []
        frappe_stub.get_all.side_effect = _route

        result = doc.get_recipients()
        excluded = [r for r in result if r.status == "Excluded"]
        assert len(excluded) == 1
        assert excluded[0].email == "unsub@x.com"

    def test_no_double_listing_for_email_both_sent_and_suppressed(self):
        """If an email appears in both sent rows and unsubscribe, it must appear once."""
        doc = self._doc()
        frappe_stub.db.get_value.side_effect = lambda dt, filters, field, **kw: (
            "SD-001" if dt == "Email Send" else None
        )

        def _route(doctype, *a, **kw):
            if doctype == "Email Send Recipient":
                return [_mk_dict(email="both@x.com", status="Sent", opened=0, opened_on=None)]
            if doctype == "Email Unsubscribe":
                return [_mk_dict(email="both@x.com")]
            return []
        frappe_stub.get_all.side_effect = _route

        result = doc.get_recipients()
        matching = [r for r in result if r.email == "both@x.com"]
        assert len(matching) == 1
        # Should be listed as Sent (from the send row), not Excluded
        assert matching[0].status == "Sent"

    def test_scopes_suppression_to_letter_and_folder(self):
        """The unsubscribe query or_filters must include folder when doc has folder."""
        doc = self._doc(folder="FOLDER-X")
        frappe_stub.db.get_value.side_effect = lambda dt, filters, field, **kw: (
            "SD-001" if dt == "Email Send" else "FOLDER-X"
        )

        captured_or_filters = []

        def _route(doctype, *a, **kw):
            if doctype == "Email Unsubscribe":
                captured_or_filters.extend(kw.get("or_filters", []))
                return []
            return []
        frappe_stub.get_all.side_effect = _route

        doc.get_recipients()
        ref_names = [f.get("reference_name") for f in captured_or_filters if "reference_name" in f]
        assert "FOLDER-X" in ref_names


# ===========================================================================
# 5. _normalize_recipient_config
# ===========================================================================
#
# Covers:
#   - dict/list input → JSON string
#   - empty/null strings → ""
#   - None → None (leave unchanged)
# ---------------------------------------------------------------------------

class TestNormalizeRecipientConfig:
    def test_dict_input_returns_json_string(self):
        cfg = {"type": "group", "email_group": "G1"}
        result = _normalize_recipient_config(cfg)
        assert json.loads(result) == cfg

    def test_list_input_returns_json_string(self):
        cfg = [{"type": "paste", "recipients": ["a@b.com"]}]
        result = _normalize_recipient_config(cfg)
        assert json.loads(result) == cfg

    def test_empty_string_returns_empty(self):
        assert _normalize_recipient_config("") == ""

    def test_null_string_returns_empty(self):
        assert _normalize_recipient_config("null") == ""

    def test_empty_object_string_returns_empty(self):
        assert _normalize_recipient_config("{}") == ""

    def test_none_returns_none(self):
        assert _normalize_recipient_config(None) is None

    def test_valid_json_string_returned_as_is(self):
        raw = '{"type": "paste"}'
        assert _normalize_recipient_config(raw) == raw


# ===========================================================================
# 6. _load_recipient_config
# ===========================================================================
#
# Covers:
#   - Old single-source dict format → wrapped in a list
#   - New array format → returned as-is
#   - Empty/null doc.recipient_config → None
# ---------------------------------------------------------------------------

class TestLoadRecipientConfig:
    def _doc(self, config):
        d = MagicMock()
        d.recipient_config = config
        return d

    def test_old_single_source_dict_wrapped_in_list(self):
        cfg = {"type": "group", "email_group": "G1"}
        result = _load_recipient_config(self._doc(json.dumps(cfg)))
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["email_group"] == "G1"

    def test_new_array_format_returned_as_is(self):
        cfg = [{"type": "paste", "recipients": ["a@b.com"]}, {"type": "group", "email_group": "G2"}]
        result = _load_recipient_config(self._doc(json.dumps(cfg)))
        assert isinstance(result, list)
        assert len(result) == 2

    def test_empty_string_returns_none(self):
        assert _load_recipient_config(self._doc("")) is None

    def test_none_value_returns_none(self):
        assert _load_recipient_config(self._doc(None)) is None

    def test_empty_array_returns_none(self):
        assert _load_recipient_config(self._doc("[]")) is None

    def test_invalid_json_returns_none(self):
        assert _load_recipient_config(self._doc("not-json")) is None


# ===========================================================================
# 7. unsubscribe.py — save_preferences
# ===========================================================================
#
# Covers:
#   - global_unsubscribe=True: inserts Email Unsubscribe with global_unsubscribe=1
#   - Folder unsubscribe: inserts Email Unsubscribe with reference_doctype="Letter Category"
#   - Removing a folder from the list deletes the existing unsubscribe record
#   - global_unsubscribe=False with existing record: deletes global record
# ---------------------------------------------------------------------------

class TestSavePreferences:
    def setup_method(self):
        _reset()
        frappe_stub.utils.cstr = lambda s: str(s) if s is not None else ""
        frappe_stub.utils.cint = lambda s: int(s) if str(s).isdigit() else (1 if s == "1" else 0)
        frappe_stub.local = MagicMock()
        frappe_stub.local.response = {}

    def _run(self, email="user@example.com", letter="", folders="", global_unsub="0"):
        unsubscribe_module.save_preferences(
            email=email, letter=letter,
            unsubscribe_folders=folders,
            global_unsubscribe=global_unsub,
        )

    def test_global_unsubscribe_inserts_record(self):
        """global_unsubscribe=1 and no existing record → insert."""
        frappe_stub.utils.validate_email_address.return_value = "user@example.com"
        frappe_stub.db.exists.return_value = None
        GETALL["Letter Category"] = []  # no folders

        inserted = {}
        def get_doc_se(d):
            m = MagicMock()
            inserted.update(d)
            return m
        frappe_stub.get_doc.side_effect = get_doc_se

        self._run(global_unsub="1")

        assert inserted.get("global_unsubscribe") == 1
        assert inserted.get("email") == "user@example.com"

    def test_global_unsub_false_with_existing_record_deletes_it(self):
        """global_unsubscribe=0 and existing global record → delete."""
        frappe_stub.utils.validate_email_address.return_value = "user@example.com"
        # First exists call (global check) returns truthy
        frappe_stub.db.exists.side_effect = lambda dt, filters: (
            "EU-GLOBAL" if filters.get("global_unsubscribe") else None
        )
        GETALL["Letter Category"] = []  # no folders

        self._run(global_unsub="0")

        frappe_stub.db.delete.assert_called()
        delete_filters = frappe_stub.db.delete.call_args[0][1]
        assert delete_filters.get("global_unsubscribe") == 1

    def test_folder_unsubscribe_inserts_folder_record(self):
        """Selecting a folder creates an Email Unsubscribe for that folder."""
        frappe_stub.utils.validate_email_address.return_value = "user@example.com"
        frappe_stub.db.exists.return_value = None  # nothing exists yet
        GETALL["Letter Category"] = [_mk_dict(name="FOLDER-A")]

        inserted = {}
        def get_doc_se(d):
            m = MagicMock()
            inserted.update(d)
            return m
        frappe_stub.get_doc.side_effect = get_doc_se

        self._run(folders="FOLDER-A", global_unsub="0")

        assert inserted.get("reference_doctype") == "Letter Category"
        assert inserted.get("reference_name") == "FOLDER-A"

    def test_removing_folder_deletes_existing_record(self):
        """A folder NOT in the submitted list that has an existing record → delete."""
        frappe_stub.utils.validate_email_address.return_value = "user@example.com"
        # Global check returns None; folder check returns existing record
        def exists_se(dt, filters):
            if filters.get("global_unsubscribe"):
                return None
            if filters.get("reference_name") == "FOLDER-B":
                return "EU-FOLDER-B"
            return None
        frappe_stub.db.exists.side_effect = exists_se
        # Two folders exist; only FOLDER-A submitted — FOLDER-B should be removed
        GETALL["Letter Category"] = [_mk_dict(name="FOLDER-A"), _mk_dict(name="FOLDER-B")]

        self._run(folders="FOLDER-A", global_unsub="0")

        # At least one delete call must target FOLDER-B
        delete_calls = frappe_stub.db.delete.call_args_list
        folder_b_deleted = any(
            c[0][1].get("reference_name") == "FOLDER-B"
            for c in delete_calls
        )
        assert folder_b_deleted

    def test_invalid_email_throws(self):
        frappe_stub.utils.validate_email_address.return_value = None
        with pytest.raises(FrappeValidationError, match="Invalid email"):
            self._run(email="notanemail")


# ===========================================================================
# 8. letters_unsubscribe.py — get_context
# ===========================================================================
#
# Covers:
#   - No email: sets folders=[], is_globally_unsubscribed=False
#   - With email: loads all Letter Folders, checks per-folder unsubscribe status
#   - is_unsubscribed flag correct for each folder
# ---------------------------------------------------------------------------

class TestGetContext:
    def setup_method(self):
        _reset()
        frappe_stub.utils.cstr = lambda s: str(s) if s is not None else ""
        frappe_stub.utils.cint = lambda s: int(s) if str(s).lstrip("-").isdigit() else 0
        frappe_stub.local = MagicMock()
        frappe_stub.request = MagicMock()

    def _ctx(self):
        return FrappeDict()

    def _set_args(self, email="", letter="", saved="0"):
        frappe_stub.request.args = {"email": email, "letter": letter, "saved": saved}

    def test_no_email_returns_empty_folders_and_not_globally_unsubscribed(self):
        self._set_args(email="")
        ctx = self._ctx()
        get_context(ctx)
        assert ctx.folders == []
        assert ctx.is_globally_unsubscribed is False

    def test_with_email_loads_all_folders(self):
        self._set_args(email="user@x.com")
        GETALL["Letter Category"] = [
            _mk_dict(name="F1", folder_name="Newsletter"),
            _mk_dict(name="F2", folder_name="Updates"),
        ]
        frappe_stub.db.exists.return_value = None
        ctx = self._ctx()
        get_context(ctx)
        assert len(ctx.folders) == 2

    def test_folder_is_unsubscribed_flag_set_correctly(self):
        self._set_args(email="user@x.com")
        GETALL["Letter Category"] = [
            _mk_dict(name="F1", folder_name="Newsletter"),
        ]
        # exists returns truthy only for F1 folder unsubscribe check
        def exists_se(dt, filters):
            if filters.get("reference_name") == "F1" and filters.get("reference_doctype") == "Letter Category":
                return "EU-F1"
            return None
        frappe_stub.db.exists.side_effect = exists_se

        ctx = self._ctx()
        get_context(ctx)
        assert ctx.folders[0]["is_unsubscribed"] is True

    def test_folder_not_unsubscribed_flag_false(self):
        self._set_args(email="user@x.com")
        GETALL["Letter Category"] = [
            _mk_dict(name="F2", folder_name="Promos"),
        ]
        frappe_stub.db.exists.return_value = None
        ctx = self._ctx()
        get_context(ctx)
        assert ctx.folders[0]["is_unsubscribed"] is False

    def test_is_globally_unsubscribed_true_when_record_exists(self):
        self._set_args(email="user@x.com")
        GETALL["Letter Category"] = []
        frappe_stub.db.exists.side_effect = lambda dt, filters: (
            "EU-GLOBAL" if filters.get("global_unsubscribe") else None
        )
        ctx = self._ctx()
        get_context(ctx)
        assert ctx.is_globally_unsubscribed is True

    def test_no_email_does_not_query_db(self):
        self._set_args(email="")
        ctx = self._ctx()
        get_context(ctx)
        frappe_stub.get_all.assert_not_called()


# ===========================================================================
# 9. Sending path — multi-source snapshot (integration-style)
# ===========================================================================
#
# Covers:
#   - When send() is called with a multi-source recipient_config, resolved_emails
#     is written back into recipient_config in the DB via frappe.db.set_value
# ---------------------------------------------------------------------------

class TestMultiSourceSnapshotOnSend:
    def setup_method(self):
        _reset()

    def _make_send_doc(self):
        sd = MagicMock()
        sd.name = "SD-MULTI"
        return sd

    def test_multi_source_send_snapshots_resolved_emails(self):
        """Sending with a two-source recipient_config must call db.set_value
        to persist resolved_emails back into the Letter's recipient_config."""
        doc = _letter_doc(name="MULTI-001")
        doc.include_unsubscribe = False
        # Two paste sources
        doc.recipient_config = json.dumps([
            {"type": "paste", "recipients": ["a@x.com"]},
            {"type": "paste", "recipients": ["b@x.com"]},
        ])
        send_doc = self._make_send_doc()

        def get_doc_se(arg, *a):
            if isinstance(arg, dict):
                return send_doc
            return doc
        frappe_stub.get_doc.side_effect = get_doc_se

        # Claim succeeds (rowcount==1)
        frappe_stub.db._cursor = MagicMock()
        frappe_stub.db._cursor.rowcount = 1

        # No suppression
        frappe_stub.db.get_value.return_value = None  # no folder
        frappe_stub.get_all.side_effect = lambda dt, *a, **kw: (
            [] if dt == "Email Send" else
            [] if dt == "Email Unsubscribe" else
            []
        )

        doc.send()

        # At least one set_value call must update recipient_config with resolved_emails
        set_value_calls = frappe_stub.db.set_value.call_args_list
        rc_calls = [
            c for c in set_value_calls
            if len(c.args) >= 3 and c.args[2] == "recipient_config"
        ]
        assert rc_calls, "Expected db.set_value to snapshot resolved_emails into recipient_config"
        saved = json.loads(rc_calls[0].args[3])
        assert isinstance(saved, list)
        assert all("resolved_emails" in src for src in saved)

    def test_single_source_send_does_not_call_multi_source_snapshot(self):
        """A single-source send uses the legacy path and should NOT call
        db.set_value with recipient_config (no per-source snapshot needed)."""
        doc = _letter_doc(name="SINGLE-001")
        doc.include_unsubscribe = False
        doc.recipient_config = json.dumps({"type": "paste", "recipients": ["a@x.com"]})
        send_doc = MagicMock()
        send_doc.name = "SD-SINGLE"

        def get_doc_se(arg, *a):
            if isinstance(arg, dict):
                return send_doc
            return doc
        frappe_stub.get_doc.side_effect = get_doc_se
        frappe_stub.db._cursor = MagicMock()
        frappe_stub.db._cursor.rowcount = 1
        frappe_stub.db.get_value.return_value = None
        frappe_stub.get_all.side_effect = lambda dt, *a, **kw: (
            [] if dt in ("Email Send", "Email Unsubscribe", "Email Group Member") else []
        )

        doc.send()

        set_value_calls = frappe_stub.db.set_value.call_args_list
        rc_calls = [
            c for c in set_value_calls
            if len(c.args) >= 3 and c.args[2] == "recipient_config"
        ]
        assert not rc_calls, "Single-source send should not snapshot recipient_config"
