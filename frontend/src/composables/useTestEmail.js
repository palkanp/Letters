import { ref } from "vue";
import { toast } from "frappe-ui";
import { describeError, stripIds } from "../utils/builderHelpers";

// Sends a single [TEST] copy of the letter to a chosen address. Prefills the
// recipient with the logged-in user's email when it looks like one.
export function useTestEmail(editorStore, { subject, previewText, flushSave }) {
  const showTestModal = ref(false);
  const testSending = ref(false);
  // Prefill with the logged-in user's email when it looks like one (it's the
  // most common test target); blank if the session id isn't an email.
  const _sessionUser = (typeof window !== "undefined" && window.frappe?.session?.user) || "";
  const testRecipient = ref(_sessionUser.includes("@") ? _sessionUser : "");

  function openTestModal() {
    if (!editorStore.blocks.length) {
      toast.warning("Canvas is empty. Add some blocks first.");
      return;
    }
    showTestModal.value = true;
  }

  async function sendTest() {
    const email = testRecipient.value.trim();
    if (!email) {
      toast.warning("Enter an email address to send the test to.");
      return;
    }
    if (editorStore.isDirty && flushSave) await flushSave();
    testSending.value = true;
    try {
      const res = await frappe.call({
        method: "letters.letters.api.send_test",
        args: {
          name:         editorStore.letterDoc?.name || null,
          blocks:       editorStore.letterDoc?.name ? null : JSON.stringify(editorStore.blocks.map(stripIds)),
          subject:      subject.value || "Test Email",
          preview_text: previewText.value,
          recipient:    email,
        },
      });
      toast.success(`Test queued to ${res.message.sent_to}. It'll arrive shortly.`);
      showTestModal.value = false;
    } catch (e) {
      toast.error("Test send failed: " + describeError(e));
    } finally {
      testSending.value = false;
    }
  }

  return { showTestModal, testSending, testRecipient, openTestModal, sendTest };
}
