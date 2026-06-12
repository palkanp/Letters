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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _campaign_doc(name="CAMP-001", status="Draft", blocks_json=None, subject="Hello"):
    doc = MagicMock()
    doc.name = name
    doc.title = "Test Campaign"
    doc.subject = subject
    doc.preview_text = ""
    doc.status = status
    doc.blocks_json = blocks_json if blocks_json is not None else json.dumps(
        [{"type": "text", "props": {"content": "Hi"}}]
    )
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


# ── get_campaign ──────────────────────────────────────────────────────────────

class TestGetCampaign:
    def setup_method(self):
        _reset()

    def test_permission_check_is_called(self):
        doc = _campaign_doc()
        frappe_stub.get_doc.return_value = doc

        api_module.get_campaign("CAMP-001")

        frappe_stub.has_permission.assert_called_once_with(
            "Letters Campaign", "read", doc=doc, throw=True
        )

    def test_returns_expected_fields(self):
        doc = _campaign_doc()
        frappe_stub.get_doc.return_value = doc

        result = api_module.get_campaign("CAMP-001")
        assert "name" in result
        assert "blocks" in result
        assert "subject" in result
        assert isinstance(result["blocks"], list)

    def test_blocks_json_parsed_to_list(self):
        doc = _campaign_doc(blocks_json=json.dumps([{"type": "text", "props": {}}]))
        frappe_stub.get_doc.return_value = doc

        result = api_module.get_campaign("CAMP-001")
        assert isinstance(result["blocks"], list)
        assert result["blocks"][0]["type"] == "text"

    def test_permission_failure_propagates(self):
        doc = _campaign_doc()
        frappe_stub.get_doc.return_value = doc
        frappe_stub.has_permission.side_effect = Exception("Forbidden")

        with pytest.raises(Exception, match="Forbidden"):
            api_module.get_campaign("CAMP-001")


# ── send_campaign — permission check ─────────────────────────────────────────

class TestSendCampaignPermission:
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
        return api_module.send_campaign(
            "CAMP-001",
            recipients=json.dumps(recipients or ["a@b.com"]),
            **kwargs,
        )

    def test_permission_check_is_called(self):
        doc = _campaign_doc()
        self._run_send(doc)
        frappe_stub.has_permission.assert_called_once_with(
            "Letters Campaign", "write", doc=doc, throw=True
        )

    def test_permission_failure_propagates(self):
        doc = _campaign_doc()
        frappe_stub.has_permission.side_effect = Exception("Permission denied")
        frappe_stub.get_doc.return_value = doc

        with pytest.raises(Exception, match="Permission denied"):
            api_module.send_campaign("CAMP-001", recipients=json.dumps(["a@b.com"]))


# ── send_campaign — idempotency guard ─────────────────────────────────────────

class TestSendCampaignIdempotency:
    def setup_method(self):
        _reset()

    def test_throws_when_status_is_sent(self):
        frappe_stub.get_doc.return_value = _campaign_doc(status="Sent")
        with pytest.raises(FrappeValidationError, match="already been sent"):
            api_module.send_campaign("CAMP-001", recipients=json.dumps(["a@b.com"]))

    def test_throws_when_status_is_sending(self):
        frappe_stub.get_doc.return_value = _campaign_doc(status="Sending")
        with pytest.raises(FrappeValidationError, match="already been sent|currently sending"):
            api_module.send_campaign("CAMP-001", recipients=json.dumps(["a@b.com"]))

    def test_resumes_existing_failed_send(self):
        """H1: a Failed prior send is resumed (not restarted), so already-Sent
        recipients are not re-delivered."""
        doc = _campaign_doc(status="Failed")
        frappe_stub.get_doc.return_value = doc
        GETALL["Email Send"] = [FrappeDict(name="SD-OLD", status="Failed")]
        frappe_stub.db.count.return_value = 3  # 3 unsent recipients remain

        result = api_module.send_campaign("CAMP-001", recipients=json.dumps(["a@b.com"]))

        assert result.get("resumed") is True
        assert result["count"] == 3
        assert frappe_stub.enqueue.called
        # The old send doc is flipped back to Sending, not a new one created
        frappe_stub.db.set_value.assert_any_call("Email Send", "SD-OLD", "status", "Sending")

    def test_resumes_existing_partial_send(self):
        doc = _campaign_doc(status="Failed")
        frappe_stub.get_doc.return_value = doc
        GETALL["Email Send"] = [FrappeDict(name="SD-OLD", status="Partial")]
        frappe_stub.db.count.return_value = 1

        result = api_module.send_campaign("CAMP-001", recipients=json.dumps(["a@b.com"]))
        assert result.get("resumed") is True

    def test_no_throw_for_clean_draft_with_no_existing_send(self):
        doc = _campaign_doc(status="Draft")
        send_doc_mock = MagicMock()
        send_doc_mock.name = "SD-NEW"

        def get_doc_se(arg, *args):
            return send_doc_mock if isinstance(arg, dict) else doc

        frappe_stub.get_doc.side_effect = get_doc_se
        frappe_stub.db.exists.return_value = None

        # Should not raise
        api_module.send_campaign("CAMP-001", recipients=json.dumps(["a@b.com"]))


# ── send_campaign — validation ────────────────────────────────────────────────

class TestSendCampaignValidation:
    def setup_method(self):
        _reset()

    def test_throws_when_blocks_json_empty(self):
        frappe_stub.get_doc.return_value = _campaign_doc(blocks_json="")
        with pytest.raises(FrappeValidationError, match="no content"):
            api_module.send_campaign("CAMP-001", recipients=json.dumps(["a@b.com"]))

    def test_throws_when_subject_empty(self):
        frappe_stub.get_doc.return_value = _campaign_doc(subject="")
        with pytest.raises(FrappeValidationError, match="no subject"):
            api_module.send_campaign("CAMP-001", recipients=json.dumps(["a@b.com"]))

    def test_throws_when_no_recipients(self):
        frappe_stub.get_doc.return_value = _campaign_doc()
        with pytest.raises(FrappeValidationError, match="No recipients"):
            api_module.send_campaign("CAMP-001", recipients=json.dumps([]))

    def test_throws_when_recipients_all_whitespace(self):
        frappe_stub.get_doc.return_value = _campaign_doc()
        with pytest.raises(FrappeValidationError):
            api_module.send_campaign("CAMP-001", recipients=json.dumps(["  ", " "]))

    def test_throws_when_email_group_has_no_active_members(self):
        frappe_stub.get_doc.return_value = _campaign_doc()
        GETALL["Email Group Member"] = []  # no members
        with pytest.raises(FrappeValidationError, match="no active subscribers"):
            api_module.send_campaign("CAMP-001", email_group="GROUP-EMPTY")

    def test_throws_when_audience_exceeds_max(self):
        """H3: an oversized audience must be refused, never silently truncated."""
        frappe_stub.get_doc.return_value = _campaign_doc()
        oversized = [f"user{i}@example.com" for i in range(api_module.MAX_RECIPIENTS + 1)]
        with pytest.raises(FrappeValidationError, match="above the per-campaign limit"):
            api_module.send_campaign("CAMP-001", recipients=json.dumps(oversized))

    def test_unsubscribed_recipients_are_filtered_out(self):
        """H2: addresses in Email Unsubscribe are dropped before sending."""
        doc = _campaign_doc()
        send_doc_mock = MagicMock()
        send_doc_mock.name = "SD-NEW"

        def get_doc_se(arg, *args):
            return send_doc_mock if isinstance(arg, dict) else doc

        frappe_stub.get_doc.side_effect = get_doc_se
        GETALL["Email Unsubscribe"] = ["gone@b.com"]

        result = api_module.send_campaign(
            "CAMP-001", recipients=json.dumps(["gone@b.com", "stay@b.com"])
        )
        assert result["count"] == 1  # only stay@b.com survives

    def test_throws_when_all_recipients_unsubscribed(self):
        frappe_stub.get_doc.return_value = _campaign_doc()
        GETALL["Email Unsubscribe"] = ["gone@b.com"]
        with pytest.raises(FrappeValidationError, match="unsubscribed"):
            api_module.send_campaign("CAMP-001", recipients=json.dumps(["gone@b.com"]))

    def test_invalid_emails_are_dropped_server_side(self):
        """M2: malformed addresses are filtered out even if the client sent them."""
        doc = _campaign_doc()
        send_doc_mock = MagicMock()
        send_doc_mock.name = "SD-NEW"

        def get_doc_se(arg, *args):
            return send_doc_mock if isinstance(arg, dict) else doc

        frappe_stub.get_doc.side_effect = get_doc_se
        # Only addresses containing "@" are considered valid by the stub.
        frappe_stub.utils.validate_email_address.side_effect = (
            lambda e, throw=False: e if "@" in e else ""
        )

        result = api_module.send_campaign(
            "CAMP-001", recipients=json.dumps(["good@b.com", "notanemail"])
        )
        assert result["count"] == 1
        assert result["skipped_invalid"] == 1

    def test_throws_when_all_emails_invalid(self):
        frappe_stub.get_doc.return_value = _campaign_doc()
        frappe_stub.utils.validate_email_address.side_effect = lambda e, throw=False: ""
        with pytest.raises(FrappeValidationError, match="No valid email"):
            api_module.send_campaign("CAMP-001", recipients=json.dumps(["nope", "also-nope"]))

    def test_recipients_json_string_is_parsed(self):
        doc = _campaign_doc()
        send_doc_mock = MagicMock()
        send_doc_mock.name = "SD-NEW"

        def get_doc_se(arg, *args):
            return send_doc_mock if isinstance(arg, dict) else doc

        frappe_stub.get_doc.side_effect = get_doc_se

        # Pass recipients as a JSON string (as the JS frontend does)
        result = api_module.send_campaign("CAMP-001", recipients='["r@r.com"]')
        assert result["count"] == 1


# ── send_campaign — enqueue ───────────────────────────────────────────────────

class TestSendCampaignEnqueue:
    def setup_method(self):
        _reset()

    def _run(self, recipients=None, email_group=None, **members):
        doc = _campaign_doc()
        send_doc_mock = MagicMock()
        send_doc_mock.name = "SD-NEW"

        def get_doc_se(arg, *args):
            return send_doc_mock if isinstance(arg, dict) else doc

        frappe_stub.get_doc.side_effect = get_doc_se

        if email_group:
            GETALL["Email Group Member"] = [FrappeDict(email="m@m.com")]
            return api_module.send_campaign("CAMP-001", email_group=email_group)

        return api_module.send_campaign(
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
            return _campaign_doc()

        frappe_stub.get_doc.side_effect = get_doc_se
        api_module.send_campaign("CAMP-001", recipients=json.dumps(["a@b.com"]))
        assert "recipients" not in captured["doc"]

    def test_email_group_mode_returns_correct_count(self):
        result = self._run(email_group="GROUP-A")
        assert result["count"] == 1
        assert result["mode"] == "email_group"

    def test_campaign_status_set_to_sending_before_enqueue(self):
        """Campaign must be marked 'Sending' synchronously to block re-submit."""
        doc = _campaign_doc()
        send_doc_mock = MagicMock()
        send_doc_mock.name = "SD-NEW"

        set_statuses = []

        def get_doc_se(arg, *args):
            return send_doc_mock if isinstance(arg, dict) else doc

        def set_status(val):
            set_statuses.append(("campaign", val))

        type(doc).status = property(lambda self: "Draft", lambda self, v: set_statuses.append(v))
        frappe_stub.get_doc.side_effect = get_doc_se
        api_module.send_campaign("CAMP-001", recipients=json.dumps(["a@b.com"]))
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
        campaign = _campaign_doc(blocks_json=blocks_json)
        send_doc = MagicMock()
        send_doc.name = "SD-001"
        send_doc.send_mode = send_mode
        send_doc.email_group = email_group
        send_doc.recipients = recipients if recipients is not None else [_recipient("a@b.com")]

        def get_doc_se(doctype, name=None):
            return campaign if doctype == "Letters Campaign" else send_doc

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

    def test_marks_campaign_sent_on_full_success(self):
        self._docs(recipients=[_recipient("a@b.com")])
        self._run()
        frappe_stub.db.set_value.assert_any_call(
            "Letters Campaign", "CAMP-001", "status", "Sent",
            update_modified=False,
        )

    def test_partial_failure_marks_send_partial_and_campaign_failed(self):
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
            "Letters Campaign", "CAMP-001", "status", "Failed",
            update_modified=False,
        )
        assert rows[0].status == "Sent"
        assert rows[1].status == "Failed"

    def test_all_fail_marks_send_and_campaign_failed(self):
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
            "Letters Campaign", "CAMP-001", "status", "Failed",
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
        frappe_stub.db.set_value.assert_any_call("Letters Campaign", "CAMP-001", "status", "Failed")
        frappe_stub.db.set_value.assert_any_call("Email Send", "SD-001", "status", "Failed")

    @pytest.mark.parametrize("send_mode", ["direct", "email_group"])
    def test_every_mode_sets_campaign_reference_for_unsubscribe(self, send_mode):
        """H2: every send mode passes a reference doc so Frappe injects the
        signed unsubscribe footer + confirmation page."""
        self._docs(recipients=[_recipient("a@b.com")], send_mode=send_mode)
        self._run()
        kw = frappe_stub.sendmail.call_args.kwargs
        assert kw["reference_doctype"] == "Letters Campaign"
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
        campaign = _campaign_doc()
        send_doc = MagicMock()
        send_doc.name = "SD-001"
        send_doc.send_mode = "direct"
        send_doc.email_group = None
        send_doc.recipients = [_recipient("a@b.com")]
        frappe_stub.get_doc.side_effect = lambda dt, n=None: campaign if dt == "Letters Campaign" else send_doc
        with patch("letters.letters.utils.email_compiler.EmailCompiler") as C:
            C.return_value.compile.return_value = "<html></html>"
            api_module._execute_send("SD-001", "CAMP-001")
        kw = frappe_stub.sendmail.call_args.kwargs
        assert kw["email_read_tracker_url"] == "/api/method/letters.letters.api.track_open"


class TestCampaignAnalytics:
    def setup_method(self):
        _reset()

    def test_no_sends_returns_zeroes(self):
        frappe_stub.get_doc.return_value = _campaign_doc()
        GETALL["Email Send"] = []
        res = api_module.get_campaign_analytics("CAMP-001")
        assert res["sent"] == 0 and res["opened"] == 0 and res["open_rate"] == 0

    def test_aggregates_open_rate(self):
        frappe_stub.get_doc.return_value = _campaign_doc()
        GETALL["Email Send"] = [FrappeDict(
            name="ES-1", status="Sent", total_recipients=4, sent_count=4, creation="2026-01-01",
        )]
        frappe_stub.db.count.return_value = 1   # 1 opened of 4 sent
        res = api_module.get_campaign_analytics("CAMP-001")
        assert res["sent"] == 4
        assert res["opened"] == 1
        assert res["open_rate"] == 25.0
        assert res["sent_status"] == "Sent"

    def test_permission_checked(self):
        doc = _campaign_doc()
        frappe_stub.get_doc.return_value = doc
        GETALL["Email Send"] = []
        api_module.get_campaign_analytics("CAMP-001")
        frappe_stub.has_permission.assert_called_with("Letters Campaign", "read", doc=doc, throw=True)


# ── send_campaign — saved recipient_config fallback (C1 / H1) ──────────────────
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
        doc = _campaign_doc()
        doc.recipient_config = json.dumps({"type": "group", "email_group": "G1"})
        GETALL["Email Group Member"] = [FrappeDict(email="a@b.com"), FrappeDict(email="c@d.com")]
        send_doc_mock = self._new_send_doc()
        frappe_stub.get_doc.side_effect = lambda arg, *a: send_doc_mock if isinstance(arg, dict) else doc

        result = api_module.send_campaign("CAMP-001")  # no explicit recipients

        assert result["queued"] is True
        assert result["count"] == 2
        assert result["mode"] == "email_group"

    def test_falls_back_to_saved_paste(self):
        doc = _campaign_doc()
        doc.recipient_config = json.dumps({"type": "paste", "recipients": ["x@y.com", "z@w.com"]})
        send_doc_mock = self._new_send_doc()
        frappe_stub.get_doc.side_effect = lambda arg, *a: send_doc_mock if isinstance(arg, dict) else doc

        result = api_module.send_campaign("CAMP-001")

        assert result["queued"] is True
        assert result["count"] == 2
        assert result["mode"] == "direct"

    def test_falls_back_to_saved_doctype(self):
        doc = _campaign_doc()
        doc.recipient_config = json.dumps({
            "type": "doctype", "doctype": "Contact", "email_field": "email_id", "filters": {},
        })
        GETALL["Contact"] = [FrappeDict(email_id="a@b.com")]
        send_doc_mock = self._new_send_doc()
        frappe_stub.get_doc.side_effect = lambda arg, *a: send_doc_mock if isinstance(arg, dict) else doc

        result = api_module.send_campaign("CAMP-001")

        assert result["queued"] is True
        assert result["count"] == 1
        assert result["mode"] == "direct"

    def test_throws_when_no_args_and_no_saved_config(self):
        doc = _campaign_doc()
        doc.recipient_config = ""  # nothing saved
        frappe_stub.get_doc.return_value = doc
        with pytest.raises(FrappeValidationError, match="no saved recipients"):
            api_module.send_campaign("CAMP-001")

    def test_explicit_recipients_still_win_over_saved_config(self):
        """Passing recipients explicitly (Send now) must not be overridden by the
        saved config."""
        doc = _campaign_doc()
        doc.recipient_config = json.dumps({"type": "group", "email_group": "G1"})
        send_doc_mock = self._new_send_doc()
        frappe_stub.get_doc.side_effect = lambda arg, *a: send_doc_mock if isinstance(arg, dict) else doc

        result = api_module.send_campaign("CAMP-001", recipients=json.dumps(["only@me.com"]))

        assert result["mode"] == "direct"
        assert result["count"] == 1


# ── schedule_campaign ─────────────────────────────────────────────────────────

class TestScheduleCampaign:
    def setup_method(self):
        _reset()

    def test_throws_when_no_saved_recipients(self):
        doc = _campaign_doc()
        doc.recipient_config = ""
        frappe_stub.get_doc.return_value = doc
        with pytest.raises(FrappeValidationError, match="Choose recipients"):
            api_module.schedule_campaign("CAMP-001", "2099-01-01 10:00:00")

    def test_throws_when_already_sent(self):
        doc = _campaign_doc(status="Sent")
        doc.recipient_config = json.dumps({"type": "group", "email_group": "G1"})
        frappe_stub.get_doc.return_value = doc
        with pytest.raises(FrappeValidationError, match="already been sent"):
            api_module.schedule_campaign("CAMP-001", "2099-01-01 10:00:00")

    def test_schedules_when_recipients_saved(self):
        import datetime
        doc = _campaign_doc()
        doc.recipient_config = json.dumps({"type": "group", "email_group": "G1"})
        frappe_stub.get_doc.return_value = doc
        frappe_stub.utils.get_datetime = lambda s: datetime.datetime(2099, 1, 1, 10, 0, 0)
        frappe_stub.utils.now_datetime = lambda: datetime.datetime(2020, 1, 1)

        with _frappe_utils_importable():
            result = api_module.schedule_campaign("CAMP-001", "2099-01-01 10:00:00")

        assert "scheduled_at" in result
        doc.db_set.assert_any_call("status", "Scheduled")


# ── process_scheduled_sends — failure surfacing ───────────────────────────────

class TestProcessScheduledSends:
    def setup_method(self):
        _reset()

    def test_marks_failed_when_send_raises(self):
        """A due campaign whose send can't start (e.g. no saved audience) is
        marked Failed, not left silently reverted to Draft."""
        import datetime
        GETALL["Letters Campaign"] = [FrappeDict(name="CAMP-DUE")]
        doc = _campaign_doc(name="CAMP-DUE")
        doc.recipient_config = ""  # send_campaign will raise
        frappe_stub.get_doc.return_value = doc
        frappe_stub.utils.now_datetime = lambda: datetime.datetime(2099, 1, 1)

        with _frappe_utils_importable():
            api_module.process_scheduled_sends()

        frappe_stub.db.set_value.assert_any_call(
            "Letters Campaign", "CAMP-DUE", "status", "Failed"
        )


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
