import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import { toast } from "frappe-ui";
import { describeError, stripIds } from "../utils/builderHelpers";

// The campaign document lifecycle: the editable fields that live outside the
// block tree (subject, preview text, recipients), persistence (load/save +
// debounced autosave), and the send / schedule / duplicate actions plus their
// progress polling. BuilderPage wires the returned state straight into its
// template; the editor store still owns the block tree itself.
export function useCampaign(editorStore) {
  const subject       = ref("");
  const previewText   = ref("");
  // { type, email_group | recipients | (doctype + email_field + filters) }
  const recipientConfig = ref(null);

  const saving        = ref(false);
  const savedFlash    = ref(false);
  let _savedFlashTimer = null;
  const loadingCampaign = ref(false);

  const showSettings        = ref(false);
  const showTemplatePicker  = ref(false);
  const showScheduleModal   = ref(false);

  const sending     = ref(false);
  const duplicating = ref(false);
  const scheduling  = ref(false);
  const scheduleDate = ref("");
  const scheduleTime = ref("");

  const sendProgress = ref({ status: "Queued", sent: 0, total: 0 });
  let _progressTimer = null;

  const campaignStatus = computed(() => {
    // While actively polling use live sendProgress status, otherwise campaignDoc
    if (["Sending", "Queued"].includes(sendProgress.value.status) && _progressTimer) {
      return "Sending";
    }
    return editorStore.campaignDoc?.status || null;
  });

  const minScheduleDate = computed(() => {
    const d = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
  });

  // ── Dirty tracking ──────────────────────────────────────────────────────────
  // _suppressDirty is a counter (not a boolean) so concurrent loadCampaign calls
  // each hold their own increment and don't accidentally re-enable dirty
  // tracking while another load is still in flight.
  let _suppressDirty = 0;
  watch([subject, previewText, () => editorStore.campaignName], () => {
    if (_suppressDirty === 0) editorStore.markDirty();
  });
  // Recipient selection is persisted on the campaign (so scheduled sends and
  // reloads know the audience). Deep-watch and mark dirty so autosave flushes it.
  watch(recipientConfig, () => {
    if (_suppressDirty === 0) editorStore.markDirty();
  }, { deep: true });

  // ── Auto-save (debounced 800ms) ───────────────────────────────────────────────
  // The history debounce (editor.js, 600ms) and this autosave debounce (800ms)
  // are intentionally independent: history coalesces rapid keystrokes into a
  // single undo entry first, and autosave fires slightly later.
  let _autoSaveTimer = null;
  watch(() => editorStore.isDirty, (dirty) => {
    if (!dirty) return;
    clearTimeout(_autoSaveTimer);
    _autoSaveTimer = setTimeout(() => {
      if (editorStore.isDirty && !saving.value) saveCampaign();
    }, 800);
  });

  // ── Load ────────────────────────────────────────────────────────────────────
  const urlParams   = new URLSearchParams(window.location.search);
  const initialName = urlParams.get("name");

  onMounted(async () => {
    if (initialName) {
      await loadCampaign(initialName);
      // A freshly created campaign (e.g. from the Desk form) has no blocks yet —
      // greet the user with the template picker instead of an empty canvas.
      if (!editorStore.blocks.length) showTemplatePicker.value = true;
    } else {
      // No campaign name in URL — show template picker so the user chooses a
      // starting point before seeing the canvas.
      showTemplatePicker.value = true;
    }
  });
  onUnmounted(() => clearInterval(_progressTimer));

  async function loadCampaign(name) {
    loadingCampaign.value = true;
    _suppressDirty++;
    try {
      const res = await frappe.call({ method: "letters.letters.api.get_campaign", args: { name } });
      const doc = res.message;
      editorStore.loadFromDoc(doc);
      subject.value         = doc.subject || "";
      previewText.value     = doc.preview_text || "";
      recipientConfig.value = doc.recipient_config || null;
      document.title = (doc.title || "Untitled Campaign") + " · Letters";
      // Allow one Vue flush cycle before re-enabling dirty tracking
      await Promise.resolve();
    } catch (e) {
      toast.error("Couldn't load campaign: " + describeError(e));
    } finally {
      // Always decrement, even on error, so the watcher is never permanently silenced
      _suppressDirty--;
      loadingCampaign.value = false;
    }
  }

  // Handles a template/blank choice from the picker. Two modes:
  //   - Existing campaign already loaded → apply blocks to it and save.
  //   - No campaign yet → create a new one, then load it.
  async function onTemplateSubmit(blocks) {
    if (editorStore.campaignDoc?.name) {
      editorStore.loadTemplate(blocks);
      await saveCampaign();
      showTemplatePicker.value = false;
      return;
    }

    const res = await frappe.call({
      method: "letters.letters.api.save_campaign",
      args: {
        name: null,
        title: "Untitled Campaign",
        subject: "",
        preview_text: "",
        email_width: 600,
        blocks: JSON.stringify(blocks),
        recipient_config: null,
      },
    });
    showTemplatePicker.value = false;
    await loadCampaign(res.message.name);
    const url = new URL(window.location.href);
    url.searchParams.set("name", res.message.name);
    window.history.replaceState({}, "", url.toString());
  }

  // ── Save ──────────────────────────────────────────────────────────────────────
  async function saveCampaign() {
    saving.value = true;
    try {
      const res = await frappe.call({
        method: "letters.letters.api.save_campaign",
        args: {
          name:         editorStore.campaignDoc?.name || null,
          title:        editorStore.campaignName || "Untitled Campaign",
          subject:      subject.value,
          preview_text: previewText.value,
          email_width:  editorStore.emailWidth,
          blocks:       JSON.stringify(editorStore.blocks.map(stripIds)),
          recipient_config: JSON.stringify(recipientConfig.value),
        },
      });
      const saved = res.message;
      const isNew = !editorStore.campaignDoc;
      // Always replace the full doc object so status/title stay consistent
      editorStore.campaignDoc = saved;
      if (isNew) {
        const url = new URL(window.location.href);
        url.searchParams.set("name", saved.name);
        window.history.replaceState({}, "", url.toString());
      }
      editorStore.clearDirty();
      // Keep browser tab title in sync with the campaign name
      document.title = (editorStore.campaignName || "Untitled Campaign") + " · Letters";
      // Brief "Saved" confirmation in the toolbar
      clearTimeout(_savedFlashTimer);
      savedFlash.value = true;
      _savedFlashTimer = setTimeout(() => { savedFlash.value = false; }, 2000);
    } catch (e) {
      toast.error("Couldn't save: " + describeError(e));
    } finally {
      saving.value = false;
    }
  }

  // Immediate save bound to Cmd/Ctrl+S: cancel the pending autosave first so the
  // two don't race into a double write.
  function saveNow() {
    clearTimeout(_autoSaveTimer);
    saveCampaign();
  }

  // ── Send ────────────────────────────────────────────────────────────────────
  async function sendCampaign() {
    if (!subject.value?.trim()) {
      showSettings.value = true;
      toast.warning("Add a subject line before sending.");
      return;
    }
    if (!editorStore.blocks.length) {
      toast.warning("Your canvas is empty. Add some blocks before sending.");
      return;
    }
    if (!recipientConfig.value) {
      showSettings.value = true;
      toast.warning("Choose recipients before sending.");
      return;
    }

    sending.value = true;
    try {
      const cfg  = recipientConfig.value;
      const args = { name: editorStore.campaignDoc?.name };
      if (cfg.type === "group") {
        args.email_group = cfg.email_group;
      } else if (cfg.type === "paste") {
        args.recipients = JSON.stringify(cfg.recipients);
      } else if (cfg.type === "doctype") {
        args.doctype_config = JSON.stringify({
          doctype:     cfg.doctype,
          email_field: cfg.email_field,
          filters:     cfg.filters || {},
        });
      }
      const res = await frappe.call({ method: "letters.letters.api.send_campaign", args });
      const { count, skipped_invalid } = res.message;
      let msg = `Queued for ${count} recipient${count === 1 ? "" : "s"}!`;
      if (skipped_invalid > 0) {
        msg += ` (${skipped_invalid} invalid address${skipped_invalid === 1 ? "" : "es"} skipped)`;
      }
      toast.success(msg);
      sendProgress.value = { status: "Queued", sent: 0, total: count };
      if (editorStore.campaignDoc) editorStore.campaignDoc.status = "Sending";
      _startProgressPolling();
    } catch (e) {
      const raw = e?._server_messages;
      let msg = e?.message || "Send failed. Check your outgoing mail settings.";
      if (raw) {
        try { msg = JSON.parse(JSON.parse(raw)[0]).message || msg; } catch { /* keep */ }
      }
      toast.error(msg);
    } finally {
      sending.value = false;
    }
  }

  function _startProgressPolling() {
    clearInterval(_progressTimer);
    _progressTimer = setInterval(async () => {
      if (!editorStore.campaignDoc?.name) { clearInterval(_progressTimer); return; }
      try {
        const r = await frappe.call({
          method: "letters.letters.api.get_send_progress",
          args: { name: editorStore.campaignDoc.name },
        });
        sendProgress.value = r.message;
        if (["Sent", "Failed", "Partial"].includes(r.message.status)) {
          clearInterval(_progressTimer);
          _progressTimer = null;
          // Sync final status back to campaignDoc so toolbar badge reflects it
          if (editorStore.campaignDoc) editorStore.campaignDoc.status = r.message.status;
          const label = r.message.status === "Sent" ? "Campaign sent successfully!" : `Send ${r.message.status.toLowerCase()}.`;
          toast[r.message.status === "Sent" ? "success" : "warning"](label);
        }
      } catch { clearInterval(_progressTimer); _progressTimer = null; }
    }, 2000);
  }

  // ── Schedule send ─────────────────────────────────────────────────────────────
  // Prefill the modal's date/time from a previously scheduled value.
  function openScheduleModal() {
    const existing = editorStore.campaignDoc?.scheduled_at;
    if (existing) {
      const [d, t] = existing.split(" ");
      scheduleDate.value = d || "";
      scheduleTime.value = t ? t.slice(0, 5) : "";
    }
    showScheduleModal.value = true;
  }

  async function scheduleCampaign() {
    if (!scheduleDate.value || !scheduleTime.value) return;
    if (!subject.value?.trim()) {
      showScheduleModal.value = false;
      showSettings.value = true;
      toast.warning("Add a subject line before scheduling.");
      return;
    }
    if (!recipientConfig.value) {
      showScheduleModal.value = false;
      showSettings.value = true;
      toast.warning("Choose recipients before scheduling.");
      return;
    }
    scheduling.value = true;
    try {
      // The scheduled send reads content + audience from the saved campaign, so
      // flush any pending edits before scheduling — otherwise the fire could run
      // against a stale (or recipient-less) saved state.
      if (editorStore.isDirty) {
        clearTimeout(_autoSaveTimer);
        await saveCampaign();
      }
      // Combine date (YYYY-MM-DD) + time (HH:mm or HH:mm:ss) into local datetime
      // string — Frappe server works in local time so no UTC conversion needed.
      const dt = `${scheduleDate.value} ${scheduleTime.value}`;
      await frappe.call({
        method: "letters.letters.api.schedule_campaign",
        args: { name: editorStore.campaignDoc.name, scheduled_at: dt },
      });
      // Reflect the new status locally so the toolbar shows the Scheduled badge.
      if (editorStore.campaignDoc) {
        editorStore.campaignDoc.status = "Scheduled";
        editorStore.campaignDoc.scheduled_at = dt;
      }
      toast.success(`Scheduled for ${scheduleDate.value} at ${scheduleTime.value}`);
      showScheduleModal.value = false;
      scheduleDate.value = "";
      scheduleTime.value = "";
    } catch (e) {
      toast.error("Schedule failed: " + describeError(e));
    } finally {
      scheduling.value = false;
    }
  }

  // ── Duplicate ─────────────────────────────────────────────────────────────────
  async function duplicateCampaign() {
    if (!editorStore.campaignDoc?.name) return;
    duplicating.value = true;
    try {
      const res = await frappe.call({
        method: "letters.letters.api.duplicate_campaign",
        args: { name: editorStore.campaignDoc.name },
      });
      const newName = res.message.name;
      toast.success(`Duplicated as "${res.message.title}". Opening it now.`);
      // Navigate to the new campaign in the same tab
      window.location.href = `/app/letters-builder?name=${encodeURIComponent(newName)}`;
    } catch (e) {
      toast.error("Duplicate failed: " + describeError(e));
      duplicating.value = false;
    }
  }

  return {
    // editable fields
    subject, previewText, recipientConfig,
    // ui visibility
    showSettings, showTemplatePicker, showScheduleModal,
    // status flags
    saving, savedFlash, loadingCampaign, sending, duplicating, scheduling,
    // schedule modal
    scheduleDate, scheduleTime, minScheduleDate, openScheduleModal,
    // progress
    sendProgress, campaignStatus,
    // actions
    loadCampaign, onTemplateSubmit, saveCampaign, saveNow,
    sendCampaign, scheduleCampaign, duplicateCampaign,
  };
}
