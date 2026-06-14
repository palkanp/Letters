import { ref } from "vue";
import { toast } from "frappe-ui";
import { describeError, stripIds } from "../utils/builderHelpers";

// Runs the server-side broken-link check (enqueue + poll) and applies inline
// URL fixes back into the block tree. Polling is capped at 90s and any prior
// poll is cancelled before a new run.
export function useLinkChecker(editorStore, { flushSave } = {}) {
  const showLinkChecker = ref(false);
  const linkResults = ref([]);
  const checkingLinks = ref(false);
  let _linkCheckPollTimer = null;

  async function openLinkChecker() {
    if (!editorStore.blocks.length) {
      toast.warning("Canvas is empty. Add some blocks first.");
      return;
    }
    if (editorStore.isDirty && flushSave) await flushSave();
    showLinkChecker.value = true;
    checkingLinks.value = true;
    linkResults.value = [];
    // Cancel any in-flight poll from a previous check.
    if (_linkCheckPollTimer) { clearInterval(_linkCheckPollTimer); _linkCheckPollTimer = null; }
    try {
      const args = editorStore.campaignDoc?.name
        ? { name: editorStore.campaignDoc.name }
        : { blocks: JSON.stringify(editorStore.blocks.map(stripIds)) };
      const startRes = await frappe.call({ method: "letters.letters.api.start_link_check", args });
      const jobKey = startRes.message?.job_key;
      if (!jobKey) throw new Error("No job key returned.");

      await new Promise((resolve, reject) => {
        const deadline = Date.now() + 90_000;
        _linkCheckPollTimer = setInterval(async () => {
          if (Date.now() > deadline) {
            clearInterval(_linkCheckPollTimer); _linkCheckPollTimer = null;
            reject(new Error("Link check timed out."));
            return;
          }
          try {
            const r = await frappe.call({
              method: "letters.letters.api.get_link_check_result",
              args: { job_key: jobKey },
            });
            if (r.message?.status === "done") {
              clearInterval(_linkCheckPollTimer); _linkCheckPollTimer = null;
              linkResults.value = r.message.results || [];
              resolve();
            }
          } catch (e) {
            clearInterval(_linkCheckPollTimer); _linkCheckPollTimer = null;
            reject(e);
          }
        }, 1500);
      });
    } catch (e) {
      toast.error("Link check failed: " + describeError(e));
      showLinkChecker.value = false;
    } finally {
      checkingLinks.value = false;
    }
  }

  function applyLinkFix(result) {
    const oldUrl = result.url;
    const newUrl = (result._fix || "").trim();
    if (!newUrl || newUrl === oldUrl) return;
    try { new URL(newUrl); } catch { toast.error("Enter a valid URL (include https://)."); return; }

    function fixInBlock(block) {
      if (!block) return;
      if (block.props) {
        for (const key of Object.keys(block.props)) {
          if (typeof block.props[key] === "string" && block.props[key].includes(oldUrl)) {
            block.props[key] = block.props[key].replaceAll(oldUrl, newUrl);
          }
        }
      }
      // container children
      if (Array.isArray(block.children)) block.children.forEach(fixInBlock);
      // columns block: each column has a .blocks array
      if (Array.isArray(block.columns)) {
        block.columns.forEach(col => {
          if (Array.isArray(col.blocks)) col.blocks.forEach(fixInBlock);
        });
      }
    }

    editorStore.blocks.forEach(fixInBlock);
    editorStore.markDirty();

    // Flip the row to green in the dialog
    result.url = newUrl;
    result.status = "ok";
    result.code = null;
    result._fix = "";
    toast.success("Link updated: press ⌘S to save.");
  }

  return { showLinkChecker, linkResults, checkingLinks, openLinkChecker, applyLinkFix };
}
