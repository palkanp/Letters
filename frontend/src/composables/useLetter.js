import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import { toast } from "frappe-ui";
import { describeError, stripIds } from "../utils/builderHelpers";

// The letter document lifecycle: the editable fields that live outside the
// block tree (subject, preview text, recipients), persistence (load/save +
// debounced autosave), and the send / schedule / duplicate actions plus their
// progress polling. BuilderPage wires the returned state straight into its
// template; the editor store still owns the block tree itself.
export function useLetter(editorStore, { initialName = null, skipTemplatePrompt = false, onClose = null } = {}) {
  const subject       = ref("");
  const previewText   = ref("");
  const senderName    = ref("");
  const senderEmail   = ref("");
  // { type, email_group | recipients | (doctype + email_field + filters) }
  const recipientConfig    = ref(null);
  const includeUnsubscribe = ref(false);

  const saving        = ref(false);
  const savedFlash    = ref(false);
  let _savedFlashTimer = null;
  const loadingLetter = ref(false);

  const showSettings        = ref(false);
  const showTemplatePicker  = ref(false);
  const showScheduleModal   = ref(false);
  const settingsInitialTab  = ref(null);

  const sending     = ref(false);
  const duplicating = ref(false);
  const scheduling  = ref(false);
  const savingTemplate      = ref(false);
  const showSaveAsTemplate  = ref(false);
  const templateTitle       = ref("");
  const scheduleDate = ref("");
  const scheduleTime = ref("");

  const sendProgress = ref({ status: "Queued", sent: 0, delivered: 0, failed: 0, total: 0 });
  let _progressTimer = null;
  const resuming = ref(false);
  // Stall detection: if delivery count stops moving for a while during a
  // "Sending" send, the background jobs may have been dropped (e.g. a queue
  // restart) with no exception raised, so the status never flips to Failed.
  // sendStalled drives a persistent Resume button in the toolbar — the toast
  // alone is easy to miss or dismiss, especially after a page reload.
  const sendStalled = ref(false);
  let _lastDeliveredKey = null;
  let _lastProgressAt = 0;
  let _stallToastId = null;
  // Short window: the backend's resume_send has its own guard against
  // double-queuing a send that's just slow (it checks RQ directly), so the
  // frontend can afford to flag "no movement" quickly rather than making
  // someone wait tens of seconds on every reload before Resume appears.
  const STALL_THRESHOLD_MS = 12000;

  const letterStatus = computed(() => {
    // While actively polling use live sendProgress status, otherwise letterDoc
    if (["Sending", "Queued"].includes(sendProgress.value.status) && _progressTimer) {
      return "Sending";
    }
    return editorStore.letterDoc?.status || null;
  });

  const minScheduleDate = computed(() => {
    const d = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
  });

  // ── Dirty tracking ──────────────────────────────────────────────────────────
  // _suppressDirty is a counter (not a boolean) so concurrent loadLetter calls
  // each hold their own increment and don't accidentally re-enable dirty
  // tracking while another load is still in flight.
  let _suppressDirty = 0;
  watch([subject, previewText, senderName, senderEmail, () => editorStore.letterName], () => {
    if (_suppressDirty === 0) editorStore.markDirty();
  });
  // Recipient selection is persisted on the letter (so scheduled sends and
  // reloads know the audience). Deep-watch and mark dirty so autosave flushes it.
  watch(recipientConfig, () => {
    if (_suppressDirty === 0) editorStore.markDirty();
  }, { deep: true });
  watch(includeUnsubscribe, () => {
    if (_suppressDirty === 0) editorStore.markDirty();
  });

  // ── Auto-save (debounced 800ms) ───────────────────────────────────────────────
  // The history debounce (editor.js, 600ms) and this autosave debounce (800ms)
  // are intentionally independent: history coalesces rapid keystrokes into a
  // single undo entry first, and autosave fires slightly later.
  let _autoSaveTimer = null;
  watch(() => editorStore.isDirty, (dirty) => {
    if (!dirty) return;
    clearTimeout(_autoSaveTimer);
    _autoSaveTimer = setTimeout(() => {
      if (editorStore.isDirty && !saving.value) saveLetter();
    }, 800);
  });

  // ── Load ────────────────────────────────────────────────────────────────────
  // Read letter name from the Frappe route: /app/letter-builder/<name>
  // Fall back to legacy ?name= query param so old bookmarks still work.
  function getRouteParam() {
    if (window.frappe?.get_route) {
      const route = frappe.get_route();
      if (route && route[1]) return route[1];
    }
    return new URLSearchParams(window.location.search).get("name");
  }

  function setRouteParam(name) {
    if (window.frappe?.set_route) {
      // replace_route: syncing the URL after a load, not a new navigation —
      // pushState here would stack a redundant history entry on top of
      // App.vue's own route sync, breaking the browser back button.
      frappe.route_flags.replace_route = true;
      frappe.set_route("letter-builder", name);
    } else {
      const url = new URL(window.location.href);
      url.searchParams.set("name", name);
      window.history.replaceState({}, "", url.toString());
    }
  }

  onMounted(async () => {
    // Capture ?tab= before setRouteParam replaces the URL and strips query params.
    const tabParam = new URLSearchParams(window.location.search).get("tab");

    // When launched from the dashboard, initialName is passed as a prop.
    // Otherwise fall back to the Frappe route / legacy query param.
    const name = initialName || getRouteParam();
    if (name) {
      // Route-based loads are silent: if the letter no longer exists (stale URL),
      // clear the route and show the template picker without any error dialogs.
      const ok = await loadLetter(name, { silent: !initialName });
      if (ok) {
        setRouteParam(name);
        // Skipped when the caller (App.vue, after the dashboard's own New
        // Letter picker) already just asked this exact question — otherwise
        // picking "Blank canvas" there immediately re-triggers this same
        // prompt the instant the builder mounts, since the letter it just
        // created has zero blocks. Looks identical to the picker that just
        // worked, making that first click look like it silently failed.
        if (!editorStore.blocks.length && !skipTemplatePrompt) showTemplatePicker.value = true;
        if (tabParam) {
          settingsInitialTab.value = tabParam;
          showSettings.value = true;
        }
      } else if (!initialName) {
        if (window.frappe?.set_route) {
          frappe.route_flags.replace_route = true;
          frappe.set_route("letter-builder");
        }
        showTemplatePicker.value = true;
      }
    } else {
      showTemplatePicker.value = true;
    }
  });
  onUnmounted(() => clearInterval(_progressTimer));

  async function loadLetter(name, { silent = false } = {}) {
    loadingLetter.value = true;
    _suppressDirty++;
    try {
      // Silent mode uses the callback form so Frappe's auto error dialog is suppressed.
      const res = await (silent
        ? new Promise((resolve, reject) =>
            frappe.call({ method: "letters.letters.api.get_letter", args: { name }, callback: resolve, error: reject })
          )
        : frappe.call({ method: "letters.letters.api.get_letter", args: { name } })
      );
      const doc = res.message;
      editorStore.loadFromDoc(doc);
      subject.value         = doc.subject || "";
      previewText.value     = doc.preview_text || "";
      senderName.value      = doc.sender_name || "";
      senderEmail.value     = doc.sender_email || "";
      recipientConfig.value    = doc.recipient_config || null;
      includeUnsubscribe.value = !!doc.include_unsubscribe;
      document.title = (doc.title || "Untitled Letter") + " · Letters";
      // A send may still be in progress from a previous session (tab reopened,
      // page reloaded) — resume live polling instead of leaving the toolbar stuck at 0/0.
      if (doc.status === "Sending") {
        sendProgress.value = { status: "Sending", sent: 0, delivered: 0, failed: 0, total: 0 };
        _startProgressPolling();
      } else if (["Partial", "Failed"].includes(doc.status)) {
        // A settled Partial/Failed send can still change later — e.g. someone
        // manually retries failed rows from the Email Queue list view, outside
        // of Letters entirely. Refresh once so the toolbar isn't stuck showing
        // whatever was true at the last settle.
        _refreshSendProgressOnce(name);
      }
      // Allow one Vue flush cycle before re-enabling dirty tracking
      await Promise.resolve();
      return true;
    } catch (e) {
      if (!silent) toast.error("Couldn't load letter: " + describeError(e));
      return false;
    } finally {
      // Always decrement, even on error, so the watcher is never permanently silenced
      _suppressDirty--;
      loadingLetter.value = false;
    }
  }

  function onTemplateClose() {
    if (editorStore.letterDoc?.name && editorStore.blocks.length) {
      // Letter exists and has content — just dismiss the picker.
      showTemplatePicker.value = false;
    } else {
      // No letter yet, or letter is empty — go back to dashboard.
      onClose?.();
    }
  }

  // Handles a template/blank choice from the picker. Two modes:
  //   - Existing letter already loaded → apply blocks to it and save.
  //   - No letter yet → create a new one, then load it.
  async function onTemplateSubmit(blocks) {
    if (editorStore.letterDoc?.name) {
      editorStore.loadTemplate(blocks);
      await saveLetter();
      showTemplatePicker.value = false;
      return;
    }

    const res = await frappe.call({
      method: "letters.letters.api.save_letter",
      args: {
        name: null,
        title: "Untitled Letter",
        subject: "",
        preview_text: "",
        email_width: 600,
        canvas_background: "#ffffff",
        blocks: JSON.stringify(blocks),
        recipient_config: null,
      },
    });
    showTemplatePicker.value = false;
    await loadLetter(res.message.name);
    setRouteParam(res.message.name);
  }

  // ── Save ──────────────────────────────────────────────────────────────────────
  async function saveLetter() {
    if (editorStore.isReadOnly) return;
    // Never create a letter from autosave — initial creation is handled by
    // onTemplateSubmit. Without this guard, null name → HTTP '' → backend creates
    // a phantom letter and the original is never updated.
    if (!editorStore.letterDoc?.name) return;
    saving.value = true;
    try {
      const res = await frappe.call({
        method: "letters.letters.api.save_letter",
        args: {
          name:         editorStore.letterDoc?.name || null,
          title:        editorStore.letterName || "Untitled Letter",
          subject:      subject.value,
          preview_text: previewText.value,
          sender_name:  senderName.value,
          sender_email: senderEmail.value,
          email_width:        editorStore.emailWidth,
          canvas_background:  editorStore.canvasBg,
          blocks:               JSON.stringify(editorStore.blocks.map(stripIds)),
          recipient_config:     JSON.stringify(recipientConfig.value),
          include_unsubscribe:  includeUnsubscribe.value,
        },
      });
      const saved = res.message;
      // Always replace the full doc object so status/title stay consistent
      editorStore.letterDoc = saved;
      setRouteParam(saved.name);
      editorStore.clearDirty();
      // Keep browser tab title in sync with the letter name
      document.title = (editorStore.letterName || "Untitled Letter") + " · Letters";
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
    saveLetter();
  }

  // ── Send ────────────────────────────────────────────────────────────────────
  async function sendLetter() {
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

    // Flush any pending autosave so the backend sends the current editor state.
    if (editorStore.isDirty) {
      clearTimeout(_autoSaveTimer);
      await saveLetter();
    }

    sending.value = true;
    try {
      const cfg  = recipientConfig.value;
      const args = { name: editorStore.letterDoc?.name };
      // Array = multi-source config already saved; backend reads it directly.
      // Single-object (legacy) = pass individual args for backward compat.
      if (!Array.isArray(cfg)) {
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
      }
      const res = await frappe.call({ method: "letters.letters.api.send_letter", args });
      const { count, skipped_invalid } = res.message;
      let msg = `Queued for ${count} recipient${count === 1 ? "" : "s"}!`;
      if (skipped_invalid > 0) {
        msg += ` (${skipped_invalid} invalid address${skipped_invalid === 1 ? "" : "es"} skipped)`;
      }
      toast.success(msg);
      sendProgress.value = { status: "Queued", sent: 0, delivered: 0, failed: 0, total: count };
      if (editorStore.letterDoc) editorStore.letterDoc.status = "Sending";
      _startProgressPolling();
    } catch (e) {
      if (editorStore.letterDoc) editorStore.letterDoc.status = "Draft";
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

  async function _refreshSendProgressOnce(name) {
    try {
      const r = await frappe.call({
        method: "letters.letters.api.get_send_progress",
        args: { name },
      });
      sendProgress.value = r.message;
      if (editorStore.letterDoc && r.message.status !== editorStore.letterDoc.status) {
        editorStore.letterDoc.status = r.message.status;
      }
      // The backend may have just settled this to "Sending" again (a retry
      // brought failed rows back to life) — pick up live polling if so.
      if (r.message.status === "Sending") _startProgressPolling();
    } catch {
      // Best-effort refresh; leave the last-known progress on the toolbar.
    }
  }

  function _startProgressPolling() {
    clearInterval(_progressTimer);
    _lastDeliveredKey = null;
    _lastProgressAt = Date.now();
    const tick = async () => {
      if (!editorStore.letterDoc?.name) { clearInterval(_progressTimer); return; }
      try {
        const r = await frappe.call({
          method: "letters.letters.api.get_send_progress",
          args: { name: editorStore.letterDoc.name },
        });
        sendProgress.value = r.message;

        if (r.message.status === "Failed" && r.message.delivered === 0) {
          // A send that failed outright (no partial delivery) is resumable.
          sendStalled.value = true;
          _offerResume("This send failed. Resume where it left off?");
        }

        if (r.message.status === "Sending") {
          const key = `${r.message.delivered}:${r.message.failed}`;
          if (key !== _lastDeliveredKey) {
            _lastDeliveredKey = key;
            _lastProgressAt = Date.now();
            sendStalled.value = false;
            if (_stallToastId) { toast.dismiss(_stallToastId); _stallToastId = null; }
          } else if (Date.now() - _lastProgressAt > STALL_THRESHOLD_MS) {
            sendStalled.value = true;
            if (!_stallToastId) _offerResume("This send hasn't made progress in a while. Resume it?");
          }
        }

        if (["Sent", "Failed", "Partial"].includes(r.message.status)) {
          clearInterval(_progressTimer);
          _progressTimer = null;
          // Sync final status back to letterDoc so toolbar badge reflects it
          if (editorStore.letterDoc) editorStore.letterDoc.status = r.message.status;
          const label = r.message.status === "Sent" ? "Letter sent successfully!" : `Send ${r.message.status.toLowerCase()}.`;
          toast[r.message.status === "Sent" ? "success" : "warning"](label);
        }
      } catch { clearInterval(_progressTimer); _progressTimer = null; }
    };
    tick();
    _progressTimer = setInterval(tick, 2000);
  }

  function _offerResume(message) {
    _stallToastId = toast.warning(message, {
      duration: Infinity,
      action: { label: "Resume", onClick: resumeSend },
    });
  }

  async function resumeSend() {
    if (!editorStore.letterDoc?.name || resuming.value) return;
    resuming.value = true;
    sendStalled.value = false;
    if (_stallToastId) { toast.dismiss(_stallToastId); _stallToastId = null; }
    try {
      const r = await frappe.call({
        method: "letters.letters.api.resume_send",
        args: { name: editorStore.letterDoc.name },
      });
      toast.success(
        r.message?.requeued ? `Resumed — requeuing ${r.message.requeued} recipients.` : "Send resumed."
      );
      sendProgress.value = { ...sendProgress.value, status: "Sending" };
      if (editorStore.letterDoc) editorStore.letterDoc.status = "Sending";
      _startProgressPolling();
    } catch (e) {
      toast.error("Couldn't resume: " + describeError(e));
    } finally {
      resuming.value = false;
    }
  }

  // ── Schedule send ─────────────────────────────────────────────────────────────
  // Prefill the modal's date/time from a previously scheduled value.
  function openScheduleModal() {
    const existing = editorStore.letterDoc?.scheduled_at;
    if (existing) {
      const [d, t] = existing.split(" ");
      scheduleDate.value = d || "";
      scheduleTime.value = t ? t.slice(0, 5) : "";
    }
    showScheduleModal.value = true;
  }

  async function scheduleLetter() {
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
      // The scheduled send reads content + audience from the saved letter, so
      // flush any pending edits before scheduling — otherwise the fire could run
      // against a stale (or recipient-less) saved state.
      if (editorStore.isDirty) {
        clearTimeout(_autoSaveTimer);
        await saveLetter();
      }
      // Combine date (YYYY-MM-DD) + time (HH:mm or HH:mm:ss) into local datetime
      // string — Frappe server works in local time so no UTC conversion needed.
      const dt = `${scheduleDate.value} ${scheduleTime.value}`;
      await frappe.call({
        method: "letters.letters.api.schedule_letter",
        args: { name: editorStore.letterDoc.name, scheduled_at: dt },
      });
      // Reflect the new status locally so the toolbar shows the Scheduled badge.
      if (editorStore.letterDoc) {
        editorStore.letterDoc.status = "Scheduled";
        editorStore.letterDoc.scheduled_at = dt;
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
  async function duplicateLetter() {
    if (!editorStore.letterDoc?.name) return;
    duplicating.value = true;
    try {
      const res = await frappe.call({
        method: "letters.letters.api.duplicate_letter",
        args: { name: editorStore.letterDoc.name },
      });
      const newName = res.message.name;
      toast.success(`Duplicated as "${res.message.title}". Opening it now.`);
      // Navigate to the new letter in the same tab
      setRouteParam(newName);
    } catch (e) {
      toast.error("Duplicate failed: " + describeError(e));
      duplicating.value = false;
    }
  }

  // ── Save as Template ─────────────────────────────────────────────────────────
  function openSaveAsTemplate() {
    templateTitle.value = editorStore.letterName || "";
    showSaveAsTemplate.value = true;
  }

  async function saveAsTemplate() {
    if (!editorStore.letterDoc?.name || !templateTitle.value.trim()) return;
    savingTemplate.value = true;
    try {
      if (editorStore.isDirty) await saveLetter();
      const res = await frappe.call({
        method: "letters.letters.api.save_letter_as_template",
        args: { letter_name: editorStore.letterDoc.name, title: templateTitle.value.trim() },
      });
      toast.success(`Saved as template "${res.message.title}".`);
      showSaveAsTemplate.value = false;
    } catch (e) {
      toast.error("Couldn't save template: " + describeError(e));
    } finally {
      savingTemplate.value = false;
    }
  }

  return {
    // editable fields
    subject, previewText, senderName, senderEmail, recipientConfig, includeUnsubscribe,
    // ui visibility
    showSettings, showTemplatePicker, showScheduleModal, settingsInitialTab,
    showSaveAsTemplate, templateTitle,
    // status flags
    saving, savedFlash, loadingLetter, sending, duplicating, scheduling, savingTemplate,
    // schedule modal
    scheduleDate, scheduleTime, minScheduleDate, openScheduleModal,
    // progress
    sendProgress, letterStatus, resuming, sendStalled,
    // actions
    loadLetter, onTemplateSubmit, onTemplateClose, saveLetter, saveNow,
    sendLetter, scheduleLetter, duplicateLetter, resumeSend,
    openSaveAsTemplate, saveAsTemplate,
  };
}
