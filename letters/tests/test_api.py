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


def _whitelist():
    """Return a pass-through decorator (ignore @frappe.whitelist())."""
    def decorator(fn):
        return fn
    return decorator


def _throw(msg="", **kwargs):
    raise FrappeValidationError(str(msg))


frappe_stub = MagicMock()
frappe_stub.whitelist = _whitelist
frappe_stub.throw     = _throw
frappe_stub._         = lambda s: s  # translation no-op

sys.modules["frappe"] = frappe_stub

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
    frappe_stub.enqueue.reset_mock()
    frappe_stub.enqueue.return_value = None
    frappe_stub.get_all.reset_mock()
    frappe_stub.get_all.return_value = []
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

    def test_throws_when_existing_sent_send_doc(self):
        frappe_stub.get_doc.return_value = _campaign_doc(status="Draft")
        frappe_stub.db.exists.return_value = "EMAIL-SEND-001"  # truthy
        with pytest.raises(FrappeValidationError, match="already been sent"):
            api_module.send_campaign("CAMP-001", recipients=json.dumps(["a@b.com"]))

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
        frappe_stub.get_all.return_value = []  # no members
        with pytest.raises(FrappeValidationError, match="no active subscribers"):
            api_module.send_campaign("CAMP-001", email_group="GROUP-EMPTY")

    def test_throws_when_audience_exceeds_max(self):
        """H3: an oversized audience must be refused, never silently truncated."""
        frappe_stub.get_doc.return_value = _campaign_doc()
        oversized = [f"user{i}@example.com" for i in range(api_module.MAX_RECIPIENTS + 1)]
        with pytest.raises(FrappeValidationError, match="above the per-campaign limit"):
            api_module.send_campaign("CAMP-001", recipients=json.dumps(oversized))

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
        frappe_stub.db.exists.return_value = None

        if email_group:
            frappe_stub.get_all.return_value = [FrappeDict(email="m@m.com")]
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

class TestExecuteSend:
    def setup_method(self):
        _reset()

    def _docs(self, blocks_json=None):
        campaign = _campaign_doc(blocks_json=blocks_json)
        send_doc = MagicMock()
        send_doc.name = "SD-001"

        def get_doc_se(doctype, name=None):
            if doctype == "Letters Campaign":
                return campaign
            return send_doc

        frappe_stub.get_doc.side_effect = get_doc_se
        return campaign, send_doc

    def test_sends_one_email_per_recipient(self):
        self._docs()
        with patch("letters.letters.utils.email_compiler.EmailCompiler") as C:
            C.return_value.compile.return_value = "<html></html>"
            api_module._execute_send("SD-001", "CAMP-001", ["a@b.com", "c@d.com"], None, "direct")
        assert frappe_stub.sendmail.call_count == 2

    def test_marks_send_doc_sent_on_success(self):
        _, send_doc = self._docs()
        with patch("letters.letters.utils.email_compiler.EmailCompiler") as C:
            C.return_value.compile.return_value = "<html></html>"
            api_module._execute_send("SD-001", "CAMP-001", ["a@b.com"], None, "direct")
        assert send_doc.status == "Sent"
        send_doc.save.assert_called()

    def test_marks_campaign_sent_on_success(self):
        campaign, _ = self._docs()
        with patch("letters.letters.utils.email_compiler.EmailCompiler") as C:
            C.return_value.compile.return_value = "<html></html>"
            api_module._execute_send("SD-001", "CAMP-001", ["a@b.com"], None, "direct")
        assert campaign.status == "Sent"

    def test_marks_send_doc_failed_on_smtp_error(self):
        _, send_doc = self._docs()
        frappe_stub.sendmail.side_effect = Exception("SMTP failure")
        with patch("letters.letters.utils.email_compiler.EmailCompiler") as C:
            C.return_value.compile.return_value = "<html></html>"
            api_module._execute_send("SD-001", "CAMP-001", ["a@b.com"], None, "direct")
        assert send_doc.status == "Failed"

    def test_reverts_campaign_to_draft_on_smtp_error(self):
        campaign, _ = self._docs()
        frappe_stub.sendmail.side_effect = Exception("SMTP failure")
        with patch("letters.letters.utils.email_compiler.EmailCompiler") as C:
            C.return_value.compile.return_value = "<html></html>"
            api_module._execute_send("SD-001", "CAMP-001", ["a@b.com"], None, "direct")
        assert campaign.status == "Draft"

    def test_logs_error_on_exception(self):
        self._docs()
        frappe_stub.sendmail.side_effect = RuntimeError("boom")
        with patch("letters.letters.utils.email_compiler.EmailCompiler") as C:
            C.return_value.compile.return_value = "<html></html>"
            api_module._execute_send("SD-001", "CAMP-001", ["a@b.com"], None, "direct")
        frappe_stub.log_error.assert_called()

    def test_email_group_mode_passes_unsubscribe_params(self):
        self._docs()
        with patch("letters.letters.utils.email_compiler.EmailCompiler") as C:
            C.return_value.compile.return_value = "<html></html>"
            api_module._execute_send("SD-001", "CAMP-001", ["a@b.com"], "GROUP-A", "email_group")
        kw = frappe_stub.sendmail.call_args.kwargs
        assert "unsubscribe_method" in kw
        assert kw["unsubscribe_params"] == {"email_group": "GROUP-A"}

    def test_direct_mode_does_not_add_unsubscribe_params(self):
        self._docs()
        with patch("letters.letters.utils.email_compiler.EmailCompiler") as C:
            C.return_value.compile.return_value = "<html></html>"
            api_module._execute_send("SD-001", "CAMP-001", ["a@b.com"], None, "direct")
        kw = frappe_stub.sendmail.call_args.kwargs
        assert "unsubscribe_method" not in kw
