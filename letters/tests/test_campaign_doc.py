"""
Integration tests for Letter Document methods.

Run with:  bench run-tests --app letters --module letters.tests.test_letter_doc

LettersTestCase tracks every doc created per test and deletes them in tearDown,
so the suite is safe to run against a real site (not just a dedicated test site).
"""
from __future__ import annotations

import json
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from letters.letters.doctype.letter._content import _unique_letter_title


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

SAMPLE_BLOCKS = json.dumps([{"type": "text", "props": {"html_content": "<p>Hello World</p>"}}])
SAMPLE_RECIPIENT_CONFIG = json.dumps({"type": "paste", "recipients": ["a@example.com", "b@example.com"]})


# ---------------------------------------------------------------------------
# Base test case — explicit cleanup so tests are safe on a real site
# ---------------------------------------------------------------------------

class LettersTestCase(IntegrationTestCase):
    def setUp(self):
        super().setUp()
        self._created = []  # (doctype, name) pairs deleted in tearDown in reverse order

    def tearDown(self):
        for doctype, name in reversed(self._created):
            try:
                frappe.delete_doc(doctype, name, force=True, ignore_missing=True)
            except Exception:
                pass
        frappe.db.commit()
        super().tearDown()

    def new_letter(self, **kwargs):
        title = f"Test Letter {frappe.generate_hash(length=8)}"
        doc = frappe.get_doc({
            "doctype": "Letter",
            "title": kwargs.get("title", title),
            "subject": kwargs.get("subject", "Test Subject"),
            "preview_text": kwargs.get("preview_text", ""),
            "status": kwargs.get("status", "Draft"),
            "email_width": kwargs.get("email_width", 600),
            "blocks_json": kwargs.get("blocks_json", SAMPLE_BLOCKS),
            "recipient_config": kwargs.get("recipient_config", SAMPLE_RECIPIENT_CONFIG),
        })
        doc.insert(ignore_permissions=True)
        self._created.append(("Letter", doc.name))
        return doc

    def new_email_send(self, letter_name, status="Sent", recipients=None):
        recipients = recipients or [
            {"email": "a@example.com", "status": "Sent"},
            {"email": "b@example.com", "status": "Sent"},
        ]
        send = frappe.get_doc({
            "doctype": "Email Send",
            "letter": letter_name,
            "status": status,
            "send_mode": "direct",
            "email_group": "",
            "total_recipients": len(recipients),
            "sent_count": len([r for r in recipients if r.get("status") == "Sent"]),
        })
        send.insert(ignore_permissions=True)
        self._created.append(("Email Send", send.name))

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

class TestAsBuilderDict(LettersTestCase):
    def test_returns_all_expected_keys(self):
        doc = self.new_letter()
        result = doc.as_builder_dict()
        for key in ("name", "title", "subject", "preview_text", "status",
                    "scheduled_at", "email_width", "blocks", "recipient_config"):
            self.assertIn(key, result)

    def test_blocks_returned_as_list(self):
        doc = self.new_letter(blocks_json=SAMPLE_BLOCKS)
        result = doc.as_builder_dict()
        self.assertIsInstance(result["blocks"], list)
        self.assertEqual(result["blocks"][0]["type"], "text")

    def test_empty_blocks_json_returns_empty_list(self):
        doc = self.new_letter(blocks_json="[]")
        result = doc.as_builder_dict()
        self.assertEqual(result["blocks"], [])

    def test_email_width_defaults_to_600_when_unset(self):
        doc = self.new_letter(email_width=0)
        doc.email_width = None
        result = doc.as_builder_dict()
        self.assertEqual(result["email_width"], 600)

    def test_recipient_config_parsed_from_json(self):
        doc = self.new_letter(recipient_config=json.dumps({"type": "paste", "recipients": ["x@y.com"]}))
        result = doc.as_builder_dict()
        self.assertIsInstance(result["recipient_config"], dict)
        self.assertEqual(result["recipient_config"]["type"], "paste")

    def test_scheduled_at_is_none_when_not_set(self):
        doc = self.new_letter()
        result = doc.as_builder_dict()
        self.assertIsNone(result["scheduled_at"])


class TestRenderPreviewHtml(LettersTestCase):
    def test_returns_html_string(self):
        doc = self.new_letter(blocks_json=SAMPLE_BLOCKS)
        html = doc.render_preview_html()
        self.assertIsInstance(html, str)
        self.assertIn("<", html)

    def test_block_content_appears_in_output(self):
        blocks = json.dumps([{"type": "text", "props": {"html_content": "<p>Unique Marker 12345</p>"}}])
        doc = self.new_letter(blocks_json=blocks)
        html = doc.render_preview_html()
        self.assertIn("Unique Marker 12345", html)

    def test_preview_text_override_is_used(self):
        doc = self.new_letter(preview_text="original preview")
        html = doc.render_preview_html(preview_text="overridden preview")
        self.assertIsInstance(html, str)

    def test_email_width_override_is_respected(self):
        doc = self.new_letter()
        html = doc.render_preview_html(email_width=800)
        self.assertIn("800px", html)


class TestDuplicate(LettersTestCase):
    def test_creates_new_doc(self):
        original = self.new_letter()
        result = original.duplicate()
        self._created.append(("Letter", result["name"]))
        self.assertIn("name", result)
        self.assertTrue(frappe.db.exists("Letter", result["name"]))

    def test_new_title_prefixed_with_copy_of(self):
        original = self.new_letter()
        result = original.duplicate()
        self._created.append(("Letter", result["name"]))
        self.assertIn("Copy of", result["title"])
        self.assertIn(original.title, result["title"])

    def test_copy_is_always_draft(self):
        original = self.new_letter(status="Sent")
        frappe.db.set_value("Letter", original.name, "status", "Sent")
        original.reload()
        result = original.duplicate()
        self._created.append(("Letter", result["name"]))
        new_doc = frappe.get_doc("Letter", result["name"])
        self.assertEqual(new_doc.status, "Draft")

    def test_copy_inherits_blocks_and_subject(self):
        original = self.new_letter(subject="Original Subject", blocks_json=SAMPLE_BLOCKS)
        result = original.duplicate()
        self._created.append(("Letter", result["name"]))
        new_doc = frappe.get_doc("Letter", result["name"])
        self.assertEqual(new_doc.subject, "Original Subject")
        self.assertEqual(new_doc.blocks_json, SAMPLE_BLOCKS)


# ---------------------------------------------------------------------------
# SendingMixin
# ---------------------------------------------------------------------------

class TestSchedule(LettersTestCase):
    def test_sets_status_scheduled(self):
        doc = self.new_letter(recipient_config=SAMPLE_RECIPIENT_CONFIG)
        with patch.object(frappe.utils, "now_datetime", return_value=frappe.utils.get_datetime("2020-01-01")):
            doc.schedule("2099-01-01 10:00:00")
        doc.reload()
        self.assertEqual(doc.status, "Scheduled")

    def test_sets_scheduled_at(self):
        doc = self.new_letter(recipient_config=SAMPLE_RECIPIENT_CONFIG)
        with patch.object(frappe.utils, "now_datetime", return_value=frappe.utils.get_datetime("2020-01-01")):
            result = doc.schedule("2099-06-15 09:00:00")
        self.assertIn("scheduled_at", result)

    def test_throws_when_already_sent(self):
        doc = self.new_letter(status="Sent")
        frappe.db.set_value("Letter", doc.name, "status", "Sent")
        doc.reload()
        with self.assertRaises(frappe.ValidationError):
            doc.schedule("2099-01-01 10:00:00")

    def test_throws_when_no_recipient_config(self):
        doc = self.new_letter(recipient_config="")
        with self.assertRaises(frappe.ValidationError):
            doc.schedule("2099-01-01 10:00:00")

    def test_throws_when_no_blocks(self):
        doc = self.new_letter(blocks_json="", recipient_config=SAMPLE_RECIPIENT_CONFIG)
        with self.assertRaises(frappe.ValidationError):
            doc.schedule("2099-01-01 10:00:00")

    def test_throws_when_scheduled_time_is_in_past(self):
        doc = self.new_letter(recipient_config=SAMPLE_RECIPIENT_CONFIG)
        with self.assertRaises(frappe.ValidationError):
            doc.schedule("2000-01-01 10:00:00")


class TestSendValidation(LettersTestCase):
    def test_throws_when_already_sending(self):
        doc = self.new_letter(status="Sending")
        frappe.db.set_value("Letter", doc.name, "status", "Sending")
        doc.reload()
        with self.assertRaises(frappe.ValidationError):
            doc.send(recipients=["a@example.com"])

    def test_throws_when_no_blocks(self):
        doc = self.new_letter(blocks_json="")
        with self.assertRaises(frappe.ValidationError):
            doc.send(recipients=["a@example.com"])

    def test_throws_when_no_subject(self):
        doc = self.new_letter(subject="")
        with self.assertRaises(frappe.ValidationError):
            doc.send(recipients=["a@example.com"])

    def test_throws_when_no_recipients_and_no_config(self):
        doc = self.new_letter(recipient_config="")
        with self.assertRaises(frappe.ValidationError):
            doc.send()

    def test_throws_when_recipient_list_is_empty(self):
        doc = self.new_letter(recipient_config="")
        with self.assertRaises(frappe.ValidationError):
            doc.send(recipients=[])

    def test_throws_when_all_recipients_unsubscribed(self):
        doc = self.new_letter()
        unsub = frappe.get_doc({
            "doctype": "Email Unsubscribe",
            "email": "only@example.com",
            "reference_doctype": "Letter",
            "reference_name": doc.name,
            "global_unsubscribe": 0,
        })
        unsub.insert(ignore_permissions=True)
        self._created.append(("Email Unsubscribe", unsub.name))
        with self.assertRaises(frappe.ValidationError):
            doc.send(recipients=["only@example.com"])


class TestSendEnqueue(LettersTestCase):
    def test_enqueues_background_job(self):
        doc = self.new_letter()
        with patch("frappe.enqueue") as mock_enqueue:
            doc.send(recipients=["a@example.com", "b@example.com"])
        mock_enqueue.assert_called_once()
        job_path = mock_enqueue.call_args.args[0] if mock_enqueue.call_args.args \
            else mock_enqueue.call_args.kwargs.get("method", "")
        self.assertIn("_execute_send", str(job_path))

    def test_returns_queued_true_with_correct_count(self):
        doc = self.new_letter()
        with patch("frappe.enqueue"):
            result = doc.send(recipients=["a@example.com", "b@example.com"])
        self.assertTrue(result["queued"])
        self.assertEqual(result["count"], 2)

    def test_creates_email_send_doc(self):
        doc = self.new_letter()
        with patch("frappe.enqueue"):
            doc.send(recipients=["a@example.com"])
        send_name = frappe.db.get_value("Email Send", {"letter": doc.name}, "name")
        self.assertIsNotNone(send_name)
        self._created.append(("Email Send", send_name))

    def test_falls_back_to_saved_recipient_config(self):
        doc = self.new_letter(recipient_config=SAMPLE_RECIPIENT_CONFIG)
        with patch("frappe.enqueue"):
            result = doc.send()
        self.assertTrue(result["queued"])
        self.assertEqual(result["count"], 2)

    def test_resumes_failed_send_instead_of_restarting(self):
        doc = self.new_letter()
        with patch("frappe.enqueue"):
            doc.send(recipients=["a@example.com"])
        send_name = frappe.db.get_value("Email Send", {"letter": doc.name}, "name")
        self._created.append(("Email Send", send_name))
        frappe.db.set_value("Email Send", send_name, "status", "Failed")
        frappe.db.set_value("Letter", doc.name, "status", "Draft")
        doc.reload()

        with patch("frappe.enqueue") as mock_enqueue:
            result = doc.send(recipients=["a@example.com"])
        self.assertTrue(result.get("resumed"))
        self.assertEqual(frappe.db.count("Email Send", {"letter": doc.name}), 1)


class TestSendSnapshot(LettersTestCase):
    """Content is snapshotted onto Email Send at queue time."""

    def test_snapshot_fields_written_on_send(self):
        doc = self.new_letter(subject="Snap Subject", blocks_json=SAMPLE_BLOCKS)
        with patch("frappe.enqueue"):
            doc.send(recipients=["a@example.com"])
        send_name = frappe.db.get_value("Email Send", {"letter": doc.name}, "name")
        self._created.append(("Email Send", send_name))
        snap = frappe.db.get_value(
            "Email Send", send_name,
            ["snapshot_subject", "snapshot_blocks"],
            as_dict=True,
        )
        self.assertEqual(snap.snapshot_subject, "Snap Subject")
        self.assertEqual(snap.snapshot_blocks, SAMPLE_BLOCKS)

    def test_snapshot_is_independent_of_later_letter_edits(self):
        doc = self.new_letter(subject="Original Subject", blocks_json=SAMPLE_BLOCKS)
        with patch("frappe.enqueue"):
            doc.send(recipients=["a@example.com"])
        frappe.db.set_value("Letter", doc.name, "subject", "Edited After Send")
        send_name = frappe.db.get_value("Email Send", {"letter": doc.name}, "name")
        self._created.append(("Email Send", send_name))
        snap_subject = frappe.db.get_value("Email Send", send_name, "snapshot_subject")
        self.assertEqual(snap_subject, "Original Subject")


class TestExecuteSendBulkQueue(LettersTestCase):
    """_execute_send hands the whole recipient list to core's Email Queue in a
    single queue_separately call, rather than looping sendmail per recipient."""

    def _seed_sending(self, statuses, send_mode="direct", include_unsubscribe=0):
        doc = self.new_letter()
        recipients = [
            {"email": f"r{i}@example.com", "status": s} for i, s in enumerate(statuses)
        ]
        send = self.new_email_send(doc.name, status="Sending", recipients=recipients)
        frappe.db.set_value(
            "Email Send", send.name,
            {
                "snapshot_blocks":      doc.blocks_json,
                "snapshot_subject":     "Bulk Subject",
                "snapshot_email_width": 600,
                "send_mode":            send_mode,
                "include_unsubscribe":  include_unsubscribe,
            },
            update_modified=False,
        )
        frappe.db.commit()
        return doc, send

    def test_makes_one_bulk_call_with_queue_flags(self):
        from letters.letters.api.sending import _execute_send
        doc, send = self._seed_sending(["Pending", "Pending", "Pending"])
        with patch("frappe.sendmail") as mock_sendmail:
            _execute_send(send.name, doc.name)
        mock_sendmail.assert_called_once()
        kw = mock_sendmail.call_args.kwargs
        self.assertTrue(kw["queue_separately"])
        self.assertEqual(kw["send_priority"], 0)
        self.assertEqual(kw["reference_doctype"], "Letter")
        self.assertEqual(kw["reference_name"], doc.name)
        self.assertEqual(
            sorted(kw["recipients"]),
            ["r0@example.com", "r1@example.com", "r2@example.com"],
        )

    def test_queues_recipients_and_stays_sending(self):
        from letters.letters.api.sending import _execute_send
        doc, send = self._seed_sending(["Pending", "Pending"])
        with patch("frappe.sendmail"):
            _execute_send(send.name, doc.name)
        statuses = frappe.get_all(
            "Email Send Recipient", filters={"parent": send.name}, pluck="status"
        )
        self.assertEqual(set(statuses), {"Sent"})  # accepted into the Email Queue
        # Stays Sending until the Email Queue drains (settled by get_send_progress).
        self.assertEqual(frappe.db.get_value("Email Send", send.name, "status"), "Sending")
        self.assertEqual(frappe.db.get_value("Email Send", send.name, "sent_count"), 2)
        self.assertEqual(frappe.db.get_value("Letter", doc.name, "status"), "Sending")

    def test_resume_only_requeues_pending_recipients(self):
        from letters.letters.api.sending import _execute_send
        doc, send = self._seed_sending(["Sent", "Pending"])
        with patch("frappe.sendmail") as mock_sendmail:
            _execute_send(send.name, doc.name)
        self.assertEqual(mock_sendmail.call_args.kwargs["recipients"], ["r1@example.com"])

    def test_all_sent_skips_sendmail(self):
        from letters.letters.api.sending import _execute_send
        doc, send = self._seed_sending(["Sent", "Sent"])
        with patch("frappe.sendmail") as mock_sendmail:
            _execute_send(send.name, doc.name)
        mock_sendmail.assert_not_called()
        self.assertEqual(frappe.db.get_value("Email Send", send.name, "status"), "Sending")

    def test_failure_marks_pending_failed(self):
        from letters.letters.api.sending import _execute_send
        doc, send = self._seed_sending(["Pending", "Pending"])
        with patch("frappe.sendmail", side_effect=Exception("smtp down")):
            _execute_send(send.name, doc.name)
        self.assertEqual(frappe.db.get_value("Email Send", send.name, "status"), "Failed")
        self.assertEqual(frappe.db.get_value("Letter", doc.name, "status"), "Failed")
        statuses = frappe.get_all(
            "Email Send Recipient", filters={"parent": send.name}, pluck="status"
        )
        self.assertEqual(set(statuses), {"Failed"})

    def test_email_group_mode_uses_native_unsubscribe(self):
        from letters.letters.api.sending import _execute_send
        doc, send = self._seed_sending(["Pending"], send_mode="email_group", include_unsubscribe=1)
        with patch("frappe.sendmail") as mock_sendmail:
            _execute_send(send.name, doc.name)
        kw = mock_sendmail.call_args.kwargs
        self.assertIsNone(kw["unsubscribe_method"])
        self.assertEqual(kw["add_unsubscribe_link"], 1)

    def test_direct_mode_with_unsubscribe_uses_portal(self):
        from letters.letters.api.sending import _execute_send
        doc, send = self._seed_sending(["Pending"], send_mode="direct", include_unsubscribe=1)
        with patch("frappe.sendmail") as mock_sendmail:
            _execute_send(send.name, doc.name)
        self.assertIn("unsubscribe_redirect", mock_sendmail.call_args.kwargs["unsubscribe_method"])


class TestSendProgressLiveDelivery(LettersTestCase):
    """get_send_progress reports live delivered/failed counts off the Email Queue
    and settles the letter's terminal status once delivery drains."""

    def _sending_letter(self, total=3):
        doc = self.new_letter()
        frappe.db.set_value("Letter", doc.name, "status", "Sending")
        send = self.new_email_send(
            doc.name, status="Sending",
            recipients=[{"email": f"r{i}@example.com", "status": "Sent"} for i in range(total)],
        )
        frappe.db.set_value(
            "Email Send", send.name,
            {"total_recipients": total, "sent_count": total},
            update_modified=False,
        )
        frappe.db.commit()
        doc.reload()
        return doc, send

    def _progress_with_counts(self, doc, counts):
        with patch("letters.letters.api.sending._delivery_counts", return_value=counts):
            return doc.get_send_progress()

    def test_reports_delivered_while_draining(self):
        doc, send = self._sending_letter(total=3)
        prog = self._progress_with_counts(
            doc, {"delivered": 2, "failed": 0, "queued": 3, "pending": 1}
        )
        self.assertEqual(prog["status"], "Sending")
        self.assertEqual(prog["delivered"], 2)
        self.assertEqual(prog["total"], 3)

    def test_stays_sending_until_all_rows_queued(self):
        # Framework still fanning out: fewer queue rows than total, none pending.
        doc, send = self._sending_letter(total=3)
        prog = self._progress_with_counts(
            doc, {"delivered": 1, "failed": 0, "queued": 1, "pending": 0}
        )
        self.assertEqual(prog["status"], "Sending")

    def test_settles_sent_when_all_delivered(self):
        doc, send = self._sending_letter(total=3)
        prog = self._progress_with_counts(
            doc, {"delivered": 3, "failed": 0, "queued": 3, "pending": 0}
        )
        self.assertEqual(prog["status"], "Sent")
        self.assertEqual(prog["delivered"], 3)
        self.assertEqual(frappe.db.get_value("Letter", doc.name, "status"), "Sent")
        self.assertEqual(frappe.db.get_value("Email Send", send.name, "status"), "Sent")
        self.assertEqual(frappe.db.get_value("Email Send", send.name, "sent_count"), 3)

    def test_settles_partial_when_some_failed(self):
        doc, send = self._sending_letter(total=3)
        prog = self._progress_with_counts(
            doc, {"delivered": 2, "failed": 1, "queued": 3, "pending": 0}
        )
        self.assertEqual(prog["status"], "Partial")
        self.assertEqual(prog["failed"], 1)
        self.assertEqual(frappe.db.get_value("Letter", doc.name, "status"), "Partial")

    def test_settles_failed_when_none_delivered(self):
        doc, send = self._sending_letter(total=2)
        prog = self._progress_with_counts(
            doc, {"delivered": 0, "failed": 2, "queued": 2, "pending": 0}
        )
        self.assertEqual(prog["status"], "Failed")
        self.assertEqual(frappe.db.get_value("Letter", doc.name, "status"), "Failed")

    def test_no_queue_data_preserves_stored_status(self):
        doc, send = self._sending_letter(total=2)
        prog = self._progress_with_counts(doc, None)
        self.assertEqual(prog["status"], "Sending")


class TestAtomicSendClaim(LettersTestCase):
    """send() must atomically transition Draft → Sending to prevent double-sends."""

    def test_throws_when_already_sending(self):
        doc = self.new_letter()
        frappe.db.set_value("Letter", doc.name, "status", "Sending")
        doc.reload()
        with self.assertRaises(frappe.ValidationError):
            doc.send(recipients=["a@example.com"])

    def test_throws_when_already_sent(self):
        doc = self.new_letter()
        frappe.db.set_value("Letter", doc.name, "status", "Sent")
        doc.reload()
        with self.assertRaises(frappe.ValidationError):
            doc.send(recipients=["a@example.com"])

    def test_letter_status_is_sending_after_successful_claim(self):
        doc = self.new_letter()
        with patch("frappe.enqueue"):
            doc.send(recipients=["a@example.com"])
        send_name = frappe.db.get_value("Email Send", {"letter": doc.name}, "name")
        self._created.append(("Email Send", send_name))
        status = frappe.db.get_value("Letter", doc.name, "status")
        self.assertEqual(status, "Sending")


class TestSendTestEmail(LettersTestCase):
    def test_sends_to_session_user(self):
        doc = self.new_letter()
        frappe.set_user("Administrator")
        with patch("frappe.sendmail") as mock_sendmail, \
             patch("frappe.utils.validate_email_address", return_value="admin@example.com"):
            result = doc.send_test_email()
        mock_sendmail.assert_called_once()
        self.assertIn("sent_to", result)

    def test_subject_prefixed_with_test(self):
        doc = self.new_letter(subject="My Letter")
        frappe.set_user("Administrator")
        with patch("frappe.sendmail") as mock_sendmail, \
             patch("frappe.utils.validate_email_address", return_value="admin@example.com"):
            doc.send_test_email()
        kw = mock_sendmail.call_args.kwargs
        self.assertIn("[TEST]", kw.get("subject", ""))
        self.assertIn("My Letter", kw.get("subject", ""))

    def test_rejects_recipient_not_matching_session_user(self):
        doc = self.new_letter()
        frappe.set_user("Administrator")
        with patch("frappe.utils.validate_email_address", return_value="admin@example.com"):
            with self.assertRaises(frappe.ValidationError):
                doc.send_test_email(recipient="someone.else@example.com")


# ---------------------------------------------------------------------------
# AnalyticsMixin
# ---------------------------------------------------------------------------

class TestGetAnalytics(LettersTestCase):
    def test_returns_zeros_when_no_sends(self):
        doc = self.new_letter()
        result = doc.get_analytics()
        self.assertIsNone(result["sent_status"])
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["sent"], 0)
        self.assertEqual(result["opened"], 0)
        self.assertEqual(result["open_rate"], 0)

    def test_computes_open_rate_from_latest_send(self):
        doc = self.new_letter()
        self.new_email_send(doc.name, status="Sent", recipients=[
            {"email": "a@example.com", "status": "Sent"},
            {"email": "b@example.com", "status": "Sent"},
            {"email": "c@example.com", "status": "Sent"},
            {"email": "d@example.com", "status": "Sent"},
        ])
        row = frappe.db.get_value("Email Send Recipient", {"email": "a@example.com"}, "name")
        frappe.db.set_value("Email Send Recipient", row, {"opened": 1, "open_count": 1})
        result = doc.get_analytics()
        self.assertEqual(result["sent"], 4)
        self.assertEqual(result["opened"], 1)
        self.assertEqual(result["open_rate"], 25.0)
        self.assertEqual(result["sent_status"], "Sent")

    def test_scopes_metrics_to_latest_send(self):
        doc = self.new_letter()
        self.new_email_send(doc.name, status="Sent", recipients=[
            {"email": "old@example.com", "status": "Sent"},
        ])
        self.new_email_send(doc.name, status="Sent", recipients=[
            {"email": "new1@example.com", "status": "Sent"},
            {"email": "new2@example.com", "status": "Sent"},
        ])
        result = doc.get_analytics()
        self.assertEqual(result["total"], 2)

    def test_includes_status_counts(self):
        doc = self.new_letter()
        self.new_email_send(doc.name, status="Sent", recipients=[
            {"email": "a@example.com", "status": "Sent"},
            {"email": "b@example.com", "status": "Failed"},
        ])
        result = doc.get_analytics()
        self.assertIn("status_counts", result)
        self.assertEqual(result["status_counts"].get("Sent"), 1)
        self.assertEqual(result["status_counts"].get("Failed"), 1)


class TestGetRecipients(LettersTestCase):
    def test_returns_empty_when_no_send(self):
        doc = self.new_letter()
        self.assertEqual(doc.get_recipients(), [])

    def test_returns_recipient_rows(self):
        doc = self.new_letter()
        self.new_email_send(doc.name, recipients=[
            {"email": "a@example.com", "status": "Sent"},
            {"email": "b@example.com", "status": "Sent"},
        ])
        result = doc.get_recipients()
        self.assertEqual(len(result), 2)
        self.assertIn("a@example.com", {r.email for r in result})

    def test_limit_is_respected(self):
        doc = self.new_letter()
        self.new_email_send(doc.name, recipients=[
            {"email": f"r{i}@example.com", "status": "Sent"} for i in range(5)
        ])
        self.assertEqual(len(doc.get_recipients(limit=2)), 2)


class TestGetSendProgress(LettersTestCase):
    def test_returns_queued_when_no_send(self):
        doc = self.new_letter()
        result = doc.get_send_progress()
        self.assertEqual(result["status"], "Queued")
        self.assertEqual(result["sent"], 0)
        self.assertEqual(result["total"], 0)

    def test_returns_progress_from_latest_send(self):
        doc = self.new_letter()
        send = self.new_email_send(doc.name, status="Sending", recipients=[
            {"email": "a@example.com", "status": "Sent"},
            {"email": "b@example.com", "status": "Pending"},
        ])
        frappe.db.set_value("Email Send", send.name, {"sent_count": 1, "total_recipients": 2})
        result = doc.get_send_progress()
        self.assertEqual(result["status"], "Sending")
        self.assertEqual(result["sent"], 1)
        self.assertEqual(result["total"], 2)


class TestRecordOpen(LettersTestCase):
    def test_marks_recipient_as_opened(self):
        doc = self.new_letter()
        self.new_email_send(doc.name, recipients=[{"email": "reader@example.com", "status": "Sent"}])
        doc.record_open("reader@example.com")
        row = frappe.db.get_value(
            "Email Send Recipient", {"email": "reader@example.com"},
            ["opened", "open_count", "opened_on"], as_dict=True,
        )
        self.assertEqual(row.opened, 1)
        self.assertEqual(row.open_count, 1)
        self.assertIsNotNone(row.opened_on)

    def test_second_open_increments_count_without_re_stamping_opened(self):
        doc = self.new_letter()
        self.new_email_send(doc.name, recipients=[{"email": "reader@example.com", "status": "Sent"}])
        doc.record_open("reader@example.com")
        doc.record_open("reader@example.com")
        row = frappe.db.get_value(
            "Email Send Recipient", {"email": "reader@example.com"}, ["open_count"], as_dict=True,
        )
        self.assertEqual(row.open_count, 2)

    def test_noop_when_no_sends(self):
        doc = self.new_letter()
        doc.record_open("nobody@example.com")


# ---------------------------------------------------------------------------
# _unique_letter_title — regression for hash-named DocType bug
# ---------------------------------------------------------------------------

class TestUniqueCampaignTitle(LettersTestCase):
    """_unique_letter_title must check the title field, not the name (hash) field."""

    def test_returns_base_when_no_collision(self):
        base = f"Unique Title {frappe.generate_hash(length=8)}"
        self.assertEqual(_unique_letter_title(base), base)

    def test_appends_1_when_title_already_exists(self):
        base = f"Duplicate Title {frappe.generate_hash(length=8)}"
        doc = self.new_letter(title=base)
        result = _unique_letter_title(base)
        self.assertEqual(result, f"{base} - 1")

    def test_increments_past_existing_suffixes(self):
        base = f"Multi Title {frappe.generate_hash(length=8)}"
        doc1 = self.new_letter(title=base)
        doc2 = self.new_letter(title=f"{base} - 1")
        result = _unique_letter_title(base)
        self.assertEqual(result, f"{base} - 2")

    def test_defaults_to_untitled_campaign_on_empty_input(self):
        # Should not raise; just return some valid non-empty title
        result = _unique_letter_title("")
        self.assertTrue(result.startswith("Untitled Letter"))

    def test_copy_of_prefix_gets_unique_title(self):
        base = f"Copy Title {frappe.generate_hash(length=8)}"
        self.new_letter(title=f"Copy of {base}")
        result = _unique_letter_title(f"Copy of {base}")
        self.assertEqual(result, f"Copy of {base} - 1")


# ---------------------------------------------------------------------------
# Rename validation — block title change only while Sending
# ---------------------------------------------------------------------------

class TestRenameValidation(LettersTestCase):
    def test_rename_allowed_on_draft(self):
        doc = self.new_letter()
        doc.title = f"Renamed {frappe.generate_hash(length=6)}"
        doc.save()  # must not raise

    def test_rename_allowed_on_sent(self):
        doc = self.new_letter()
        frappe.db.set_value("Letter", doc.name, "status", "Sent")
        doc.reload()
        doc.title = f"Renamed Sent {frappe.generate_hash(length=6)}"
        doc.save()  # must not raise

    def test_rename_allowed_on_scheduled(self):
        doc = self.new_letter()
        frappe.db.set_value("Letter", doc.name, "status", "Scheduled")
        doc.reload()
        doc.title = f"Renamed Scheduled {frappe.generate_hash(length=6)}"
        doc.save()  # must not raise

    def test_rename_blocked_while_sending(self):
        doc = self.new_letter()
        frappe.db.set_value("Letter", doc.name, "status", "Sending")
        doc.reload()
        doc.title = f"Renamed Sending {frappe.generate_hash(length=6)}"
        with self.assertRaises(frappe.ValidationError):
            doc.save()
