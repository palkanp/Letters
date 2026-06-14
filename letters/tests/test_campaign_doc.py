"""
Integration tests for LettersCampaign Document methods.

These tests require a running Frappe bench and test site.
Run with:  bench run-tests --app letters --module letters.tests.test_campaign_doc

Each test class is wrapped in a transaction that is rolled back after the class
(via IntegrationTestCase.setUpClass → addClassCleanup(_rollback_db)), so no
manual cleanup is needed as long as each test uses a unique campaign title.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_BLOCKS = json.dumps([{"type": "text", "props": {"html_content": "<p>Hello World</p>"}}])
SAMPLE_RECIPIENT_CONFIG = json.dumps({"type": "paste", "recipients": ["a@example.com", "b@example.com"]})


def _new_campaign(**kwargs) -> "frappe.Document":
    """Insert and return a fresh Letters Campaign with a unique title."""
    title = f"Test Campaign {frappe.generate_hash(length=8)}"
    doc = frappe.get_doc({
        "doctype": "Letters Campaign",
        "title": kwargs.get("title", title),
        "subject": kwargs.get("subject", "Test Subject"),
        "preview_text": kwargs.get("preview_text", ""),
        "status": kwargs.get("status", "Draft"),
        "email_width": kwargs.get("email_width", 600),
        "blocks_json": kwargs.get("blocks_json", SAMPLE_BLOCKS),
        "recipient_config": kwargs.get("recipient_config", SAMPLE_RECIPIENT_CONFIG),
    })
    doc.insert(ignore_permissions=True)
    return doc


def _new_email_send(campaign_name, status="Sent", recipients=None) -> "frappe.Document":
    """Create an Email Send + its recipient rows for a campaign."""
    recipients = recipients or [
        {"email": "a@example.com", "status": "Sent"},
        {"email": "b@example.com", "status": "Sent"},
    ]
    send = frappe.get_doc({
        "doctype": "Email Send",
        "campaign": campaign_name,
        "status": status,
        "send_mode": "direct",
        "email_group": "",
        "total_recipients": len(recipients),
        "sent_count": len([r for r in recipients if r.get("status") == "Sent"]),
    })
    send.insert(ignore_permissions=True)

    now = frappe.utils.now()
    user = frappe.session.user
    fields = [
        "name", "creation", "modified", "modified_by", "owner", "docstatus",
        "idx", "parent", "parentfield", "parenttype", "email", "status",
    ]
    values = [
        (
            frappe.generate_hash(length=10), now, now, user, user, 0,
            idx + 1, send.name, "recipients", "Email Send",
            r["email"], r.get("status", "Pending"),
        )
        for idx, r in enumerate(recipients)
    ]
    frappe.db.bulk_insert("Email Send Recipient", fields=fields, values=values)
    return send


# ---------------------------------------------------------------------------
# ContentMixin
# ---------------------------------------------------------------------------

class TestAsBuilderDict(IntegrationTestCase):
    def test_returns_all_expected_keys(self):
        doc = _new_campaign()
        result = doc.as_builder_dict()
        for key in ("name", "title", "subject", "preview_text", "status",
                    "scheduled_at", "email_width", "blocks", "recipient_config"):
            self.assertIn(key, result)

    def test_blocks_returned_as_list(self):
        doc = _new_campaign(blocks_json=SAMPLE_BLOCKS)
        result = doc.as_builder_dict()
        self.assertIsInstance(result["blocks"], list)
        self.assertEqual(result["blocks"][0]["type"], "text")

    def test_empty_blocks_json_returns_empty_list(self):
        doc = _new_campaign(blocks_json="[]")
        result = doc.as_builder_dict()
        self.assertEqual(result["blocks"], [])

    def test_email_width_defaults_to_600_when_unset(self):
        doc = _new_campaign(email_width=0)
        doc.email_width = None
        result = doc.as_builder_dict()
        self.assertEqual(result["email_width"], 600)

    def test_recipient_config_parsed_from_json(self):
        doc = _new_campaign(recipient_config=json.dumps({"type": "paste", "recipients": ["x@y.com"]}))
        result = doc.as_builder_dict()
        self.assertIsInstance(result["recipient_config"], dict)
        self.assertEqual(result["recipient_config"]["type"], "paste")

    def test_scheduled_at_is_none_when_not_set(self):
        doc = _new_campaign()
        result = doc.as_builder_dict()
        self.assertIsNone(result["scheduled_at"])


class TestRenderPreviewHtml(IntegrationTestCase):
    def test_returns_html_string(self):
        doc = _new_campaign(blocks_json=SAMPLE_BLOCKS)
        html = doc.render_preview_html()
        self.assertIsInstance(html, str)
        self.assertIn("<", html)

    def test_block_content_appears_in_output(self):
        blocks = json.dumps([{"type": "text", "props": {"html_content": "<p>Unique Marker 12345</p>"}}])
        doc = _new_campaign(blocks_json=blocks)
        html = doc.render_preview_html()
        self.assertIn("Unique Marker 12345", html)

    def test_preview_text_override_is_used(self):
        doc = _new_campaign(preview_text="original preview")
        # Override — the preview text goes into the email header, not necessarily
        # visible in block output, but the method should accept it without error.
        html = doc.render_preview_html(preview_text="overridden preview")
        self.assertIsInstance(html, str)

    def test_email_width_override_is_respected(self):
        doc = _new_campaign()
        html = doc.render_preview_html(email_width=800)
        self.assertIn("800px", html)


class TestDuplicate(IntegrationTestCase):
    def test_creates_new_doc(self):
        original = _new_campaign()
        result = original.duplicate()
        self.assertIn("name", result)
        self.assertTrue(frappe.db.exists("Letters Campaign", result["name"]))

    def test_new_title_prefixed_with_copy_of(self):
        original = _new_campaign()
        result = original.duplicate()
        self.assertIn("Copy of", result["title"])
        self.assertIn(original.title, result["title"])

    def test_copy_is_always_draft(self):
        original = _new_campaign(status="Sent")
        # Manually set status to Sent in DB so the duplicate reads it
        frappe.db.set_value("Letters Campaign", original.name, "status", "Sent")
        original.reload()
        result = original.duplicate()
        new_doc = frappe.get_doc("Letters Campaign", result["name"])
        self.assertEqual(new_doc.status, "Draft")

    def test_copy_inherits_blocks_and_subject(self):
        original = _new_campaign(subject="Original Subject", blocks_json=SAMPLE_BLOCKS)
        result = original.duplicate()
        new_doc = frappe.get_doc("Letters Campaign", result["name"])
        self.assertEqual(new_doc.subject, "Original Subject")
        self.assertEqual(new_doc.blocks_json, SAMPLE_BLOCKS)


# ---------------------------------------------------------------------------
# SendingMixin
# ---------------------------------------------------------------------------

class TestSchedule(IntegrationTestCase):
    def test_sets_status_scheduled(self):
        doc = _new_campaign(recipient_config=SAMPLE_RECIPIENT_CONFIG)
        with patch.object(frappe.utils, "now_datetime", return_value=frappe.utils.get_datetime("2020-01-01")):
            doc.schedule("2099-01-01 10:00:00")
        doc.reload()
        self.assertEqual(doc.status, "Scheduled")

    def test_sets_scheduled_at(self):
        doc = _new_campaign(recipient_config=SAMPLE_RECIPIENT_CONFIG)
        with patch.object(frappe.utils, "now_datetime", return_value=frappe.utils.get_datetime("2020-01-01")):
            result = doc.schedule("2099-06-15 09:00:00")
        self.assertIn("scheduled_at", result)

    def test_throws_when_already_sent(self):
        doc = _new_campaign(status="Sent")
        frappe.db.set_value("Letters Campaign", doc.name, "status", "Sent")
        doc.reload()
        with self.assertRaises(frappe.ValidationError):
            doc.schedule("2099-01-01 10:00:00")

    def test_throws_when_no_recipient_config(self):
        doc = _new_campaign(recipient_config="")
        with self.assertRaises(frappe.ValidationError):
            doc.schedule("2099-01-01 10:00:00")

    def test_throws_when_no_blocks(self):
        doc = _new_campaign(blocks_json="", recipient_config=SAMPLE_RECIPIENT_CONFIG)
        with self.assertRaises(frappe.ValidationError):
            doc.schedule("2099-01-01 10:00:00")

    def test_throws_when_scheduled_time_is_in_past(self):
        doc = _new_campaign(recipient_config=SAMPLE_RECIPIENT_CONFIG)
        with self.assertRaises(frappe.ValidationError):
            doc.schedule("2000-01-01 10:00:00")


class TestSendValidation(IntegrationTestCase):
    def test_throws_when_already_sending(self):
        doc = _new_campaign(status="Sending")
        frappe.db.set_value("Letters Campaign", doc.name, "status", "Sending")
        doc.reload()
        with self.assertRaises(frappe.ValidationError):
            doc.send(recipients=["a@example.com"])

    def test_throws_when_no_blocks(self):
        doc = _new_campaign(blocks_json="")
        with self.assertRaises(frappe.ValidationError):
            doc.send(recipients=["a@example.com"])

    def test_throws_when_no_subject(self):
        doc = _new_campaign(subject="")
        with self.assertRaises(frappe.ValidationError):
            doc.send(recipients=["a@example.com"])

    def test_throws_when_no_recipients_and_no_config(self):
        doc = _new_campaign(recipient_config="")
        with self.assertRaises(frappe.ValidationError):
            doc.send()

    def test_throws_when_recipient_list_is_empty(self):
        doc = _new_campaign(recipient_config="")
        with self.assertRaises(frappe.ValidationError):
            doc.send(recipients=[])

    def test_throws_when_all_recipients_unsubscribed(self):
        doc = _new_campaign()
        # Register an unsubscribe for every address we pass
        frappe.get_doc({
            "doctype": "Email Unsubscribe",
            "email": "only@example.com",
            "reference_doctype": "Letters Campaign",
            "reference_name": doc.name,
            "global_unsubscribe": 0,
        }).insert(ignore_permissions=True)
        with self.assertRaises(frappe.ValidationError):
            doc.send(recipients=["only@example.com"])


class TestSendEnqueue(IntegrationTestCase):
    def test_enqueues_background_job(self):
        doc = _new_campaign()
        with patch("frappe.enqueue") as mock_enqueue:
            doc.send(recipients=["a@example.com", "b@example.com"])
        mock_enqueue.assert_called_once()
        job_path = mock_enqueue.call_args.args[0] if mock_enqueue.call_args.args \
            else mock_enqueue.call_args.kwargs.get("method", "")
        self.assertIn("_execute_send", str(job_path))

    def test_returns_queued_true_with_correct_count(self):
        doc = _new_campaign()
        with patch("frappe.enqueue"):
            result = doc.send(recipients=["a@example.com", "b@example.com"])
        self.assertTrue(result["queued"])
        self.assertEqual(result["count"], 2)

    def test_creates_email_send_doc(self):
        doc = _new_campaign()
        with patch("frappe.enqueue"):
            doc.send(recipients=["a@example.com"])
        send = frappe.db.get_value("Email Send", {"campaign": doc.name}, "name")
        self.assertIsNotNone(send)

    def test_falls_back_to_saved_recipient_config(self):
        doc = _new_campaign(recipient_config=SAMPLE_RECIPIENT_CONFIG)
        with patch("frappe.enqueue"):
            result = doc.send()  # no explicit recipients
        self.assertTrue(result["queued"])
        self.assertEqual(result["count"], 2)

    def test_resumes_failed_send_instead_of_restarting(self):
        doc = _new_campaign()
        with patch("frappe.enqueue"):
            doc.send(recipients=["a@example.com"])
        # Mark the send as Failed to trigger the resume path
        send_name = frappe.db.get_value("Email Send", {"campaign": doc.name}, "name")
        frappe.db.set_value("Email Send", send_name, "status", "Failed")
        # Mark campaign back to allow retry
        frappe.db.set_value("Letters Campaign", doc.name, "status", "Draft")
        doc.reload()

        with patch("frappe.enqueue") as mock_enqueue:
            result = doc.send(recipients=["a@example.com"])
        self.assertTrue(result.get("resumed"))
        # Still the same Email Send doc, not a new one
        send_count = frappe.db.count("Email Send", {"campaign": doc.name})
        self.assertEqual(send_count, 1)


class TestSendSnapshot(IntegrationTestCase):
    """Content is snapshotted onto Email Send at queue time."""

    def test_snapshot_fields_written_on_send(self):
        doc = _new_campaign(subject="Snap Subject", blocks_json=SAMPLE_BLOCKS)
        with patch("frappe.enqueue"):
            doc.send(recipients=["a@example.com"])
        send_name = frappe.db.get_value("Email Send", {"campaign": doc.name}, "name")
        snap = frappe.db.get_value(
            "Email Send", send_name,
            ["snapshot_subject", "snapshot_blocks"],
            as_dict=True,
        )
        self.assertEqual(snap.snapshot_subject, "Snap Subject")
        self.assertEqual(snap.snapshot_blocks, SAMPLE_BLOCKS)

    def test_snapshot_is_independent_of_later_campaign_edits(self):
        doc = _new_campaign(subject="Original Subject", blocks_json=SAMPLE_BLOCKS)
        with patch("frappe.enqueue"):
            doc.send(recipients=["a@example.com"])
        # Simulate a post-send edit to the live campaign
        frappe.db.set_value("Letters Campaign", doc.name, "subject", "Edited After Send")

        send_name = frappe.db.get_value("Email Send", {"campaign": doc.name}, "name")
        snap_subject = frappe.db.get_value("Email Send", send_name, "snapshot_subject")
        self.assertEqual(snap_subject, "Original Subject")


class TestAtomicSendClaim(IntegrationTestCase):
    """send() must atomically transition Draft → Sending to prevent double-sends."""

    def test_throws_when_already_sending(self):
        doc = _new_campaign()
        frappe.db.set_value("Letters Campaign", doc.name, "status", "Sending")
        doc.reload()
        with self.assertRaises(frappe.ValidationError):
            doc.send(recipients=["a@example.com"])

    def test_throws_when_already_sent(self):
        doc = _new_campaign()
        frappe.db.set_value("Letters Campaign", doc.name, "status", "Sent")
        doc.reload()
        with self.assertRaises(frappe.ValidationError):
            doc.send(recipients=["a@example.com"])

    def test_campaign_status_is_sending_after_successful_claim(self):
        doc = _new_campaign()
        with patch("frappe.enqueue"):
            doc.send(recipients=["a@example.com"])
        status = frappe.db.get_value("Letters Campaign", doc.name, "status")
        self.assertEqual(status, "Sending")


class TestSendTestEmail(IntegrationTestCase):
    def test_sends_to_session_user(self):
        doc = _new_campaign()
        frappe.set_user("Administrator")
        with patch("frappe.sendmail") as mock_sendmail, \
             patch("frappe.utils.validate_email_address", return_value="admin@example.com"):
            result = doc.send_test_email()
        mock_sendmail.assert_called_once()
        self.assertIn("sent_to", result)

    def test_subject_prefixed_with_test(self):
        doc = _new_campaign(subject="My Campaign")
        frappe.set_user("Administrator")
        with patch("frappe.sendmail") as mock_sendmail, \
             patch("frappe.utils.validate_email_address", return_value="admin@example.com"):
            doc.send_test_email()
        kw = mock_sendmail.call_args.kwargs
        self.assertIn("[TEST]", kw.get("subject", ""))
        self.assertIn("My Campaign", kw.get("subject", ""))

    def test_rejects_recipient_not_matching_session_user(self):
        doc = _new_campaign()
        frappe.set_user("Administrator")
        with patch("frappe.utils.validate_email_address", return_value="admin@example.com"):
            with self.assertRaises(frappe.ValidationError):
                doc.send_test_email(recipient="someone.else@example.com")


# ---------------------------------------------------------------------------
# AnalyticsMixin
# ---------------------------------------------------------------------------

class TestGetAnalytics(IntegrationTestCase):
    def test_returns_zeros_when_no_sends(self):
        doc = _new_campaign()
        result = doc.get_analytics()
        self.assertIsNone(result["sent_status"])
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["sent"], 0)
        self.assertEqual(result["opened"], 0)
        self.assertEqual(result["open_rate"], 0)

    def test_computes_open_rate_from_latest_send(self):
        doc = _new_campaign()
        _new_email_send(doc.name, status="Sent", recipients=[
            {"email": "a@example.com", "status": "Sent"},
            {"email": "b@example.com", "status": "Sent"},
            {"email": "c@example.com", "status": "Sent"},
            {"email": "d@example.com", "status": "Sent"},
        ])
        # Mark one recipient as opened
        row = frappe.db.get_value(
            "Email Send Recipient",
            {"email": "a@example.com"},
            "name",
        )
        frappe.db.set_value("Email Send Recipient", row, {"opened": 1, "open_count": 1})

        result = doc.get_analytics()
        self.assertEqual(result["sent"], 4)
        self.assertEqual(result["opened"], 1)
        self.assertEqual(result["open_rate"], 25.0)
        self.assertEqual(result["sent_status"], "Sent")

    def test_scopes_metrics_to_latest_send(self):
        """Open rate should use only the most recent send as denominator."""
        doc = _new_campaign()
        _new_email_send(doc.name, status="Sent", recipients=[
            {"email": "old@example.com", "status": "Sent"},
        ])
        second_send = _new_email_send(doc.name, status="Sent", recipients=[
            {"email": "new1@example.com", "status": "Sent"},
            {"email": "new2@example.com", "status": "Sent"},
        ])
        result = doc.get_analytics()
        # Denominator should be 2 (latest send), not 3 (all sends)
        self.assertEqual(result["total"], 2)

    def test_includes_status_counts(self):
        doc = _new_campaign()
        _new_email_send(doc.name, status="Sent", recipients=[
            {"email": "a@example.com", "status": "Sent"},
            {"email": "b@example.com", "status": "Failed"},
        ])
        result = doc.get_analytics()
        self.assertIn("status_counts", result)
        self.assertEqual(result["status_counts"].get("Sent"), 1)
        self.assertEqual(result["status_counts"].get("Failed"), 1)


class TestGetRecipients(IntegrationTestCase):
    def test_returns_empty_when_no_send(self):
        doc = _new_campaign()
        result = doc.get_recipients()
        self.assertEqual(result, [])

    def test_returns_recipient_rows(self):
        doc = _new_campaign()
        _new_email_send(doc.name, recipients=[
            {"email": "a@example.com", "status": "Sent"},
            {"email": "b@example.com", "status": "Sent"},
        ])
        result = doc.get_recipients()
        self.assertEqual(len(result), 2)
        emails = {r.email for r in result}
        self.assertIn("a@example.com", emails)

    def test_limit_is_respected(self):
        doc = _new_campaign()
        _new_email_send(doc.name, recipients=[
            {"email": f"r{i}@example.com", "status": "Sent"} for i in range(5)
        ])
        result = doc.get_recipients(limit=2)
        self.assertEqual(len(result), 2)


class TestGetSendProgress(IntegrationTestCase):
    def test_returns_queued_when_no_send(self):
        doc = _new_campaign()
        result = doc.get_send_progress()
        self.assertEqual(result["status"], "Queued")
        self.assertEqual(result["sent"], 0)
        self.assertEqual(result["total"], 0)

    def test_returns_progress_from_latest_send(self):
        doc = _new_campaign()
        send = _new_email_send(doc.name, status="Sending", recipients=[
            {"email": "a@example.com", "status": "Sent"},
            {"email": "b@example.com", "status": "Pending"},
        ])
        frappe.db.set_value("Email Send", send.name, {"sent_count": 1, "total_recipients": 2})

        result = doc.get_send_progress()
        self.assertEqual(result["status"], "Sending")
        self.assertEqual(result["sent"], 1)
        self.assertEqual(result["total"], 2)


class TestRecordOpen(IntegrationTestCase):
    def test_marks_recipient_as_opened(self):
        doc = _new_campaign()
        _new_email_send(doc.name, recipients=[
            {"email": "reader@example.com", "status": "Sent"},
        ])
        doc.record_open("reader@example.com")

        row = frappe.db.get_value(
            "Email Send Recipient",
            {"email": "reader@example.com"},
            ["opened", "open_count", "opened_on"],
            as_dict=True,
        )
        self.assertEqual(row.opened, 1)
        self.assertEqual(row.open_count, 1)
        self.assertIsNotNone(row.opened_on)

    def test_second_open_increments_count_without_re_stamping_opened(self):
        doc = _new_campaign()
        _new_email_send(doc.name, recipients=[
            {"email": "reader@example.com", "status": "Sent"},
        ])
        doc.record_open("reader@example.com")
        doc.record_open("reader@example.com")

        row = frappe.db.get_value(
            "Email Send Recipient",
            {"email": "reader@example.com"},
            ["open_count"],
            as_dict=True,
        )
        self.assertEqual(row.open_count, 2)

    def test_noop_when_no_sends(self):
        doc = _new_campaign()
        # Should not raise even when there are no sends
        doc.record_open("nobody@example.com")
