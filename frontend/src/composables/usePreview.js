import { ref } from "vue";
import { toast } from "frappe-ui";
import { describeError, stripIds } from "../utils/builderHelpers";

// Opens the rendered email in a new tab with a desktop/mobile toggle toolbar.
// The window is opened synchronously (before the await) so the pop-up blocker
// doesn't kill it.
export function usePreview(editorStore, previewText) {
  const previewing = ref(false);

  async function openPreview() {
    // Open the window BEFORE the async call — browsers only allow window.open
    // inside a synchronous user-gesture handler. Opening it after an await
    // makes the popup blocker kill it silently.
    const win = window.open("", "_blank");
    if (!win) {
      toast.warning("Pop-up blocked. Allow pop-ups for this site to use Preview.");
      return;
    }

    // Show a loading indicator in the new tab while we fetch the HTML.
    win.document.write(
      "<!doctype html><html><head><title>Loading preview…</title>" +
      "<style>body{font-family:system-ui,sans-serif;display:flex;align-items:center;" +
      "justify-content:center;height:100vh;margin:0;color:#6b7280;font-size:14px;}" +
      "</style></head><body>Generating preview…</body></html>"
    );
    win.document.close();

    previewing.value = true;
    try {
      const res = await frappe.call({
        method: "letters.letters.api.render_preview",
        args: {
          // Passed alongside `blocks` (not instead of) so the preview reflects
          // unsaved canvas edits, while still letting the backend resolve
          // `{{ doc.field }}` merge tags against this Letter's linked
          // Notification, if it has one.
          name:         editorStore.letterDoc?.name,
          blocks:       JSON.stringify(editorStore.blocks.map(stripIds)),
          preview_text: previewText.value,
          email_width:  editorStore.emailWidth,
        },
      });
      const html          = res.message.html;
      const rawTitle      = editorStore.letterName || "Email Preview";
      const letterTitle = rawTitle
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");

      // Shell page: hosts the email inside an <iframe> plus the device toolbar.
      // The email must live in an iframe (not written straight into the tab) so
      // it gets its OWN viewport — that is what lets the compiled email's
      // @media (max-width:600px) rules actually fire when we shrink to mobile.
      const shell = `<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<title>${letterTitle} · Preview</title>
<style>
  html, body { margin: 0; width: 100%; height: 100%; background: #e5e7eb; overflow-x: hidden; }
  #__preview-stage {
    width: 100%; height: 100vh; display: flex; justify-content: center; align-items: stretch;
    overflow: hidden;
  }
  #__preview-frame {
    width: 100%; height: 100%; border: 0; background: #f3f4f6;
    transition: width .2s ease; box-shadow: 0 0 0 1px rgba(0,0,0,.08);
  }
  #__preview-toolbar {
    position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
    display: flex; align-items: center; gap: 4px;
    background: #111827; border-radius: 9999px;
    padding: 6px 10px; box-shadow: 0 8px 32px rgba(0,0,0,.5);
    z-index: 9999; font-family: -apple-system, sans-serif;
  }
  #__preview-toolbar span {
    color: #9ca3af; font-size: 11px; padding: 0 8px 0 4px;
    border-right: 1px solid #374151; margin-right: 4px;
  }
  #__preview-toolbar button {
    color: #e5e7eb; background: none; border: none; cursor: pointer;
    font-size: 12px; padding: 5px 12px; border-radius: 6px; transition: background .15s;
  }
  #__preview-toolbar button:hover { background: #1f2937; }
  #__preview-toolbar button.active { background: #374151; color: #fff; }
</style>
</head>
<body>
<div id="__preview-stage">
  <iframe id="__preview-frame" title="Email preview"></iframe>
</div>
<div id="__preview-toolbar">
  <span>${letterTitle}</span>
  <button class="active" onclick="setMode('desktop', this)">🖥 Desktop</button>
  <button onclick="setMode('mobile', this)">📱 Mobile</button>
</div>
<script>
  function setMode(mode, btn) {
    document.querySelectorAll('#__preview-toolbar button').forEach(function (b) { b.classList.remove('active'); });
    btn.classList.add('active');
    // Resizing the IFRAME (not the body) narrows its viewport, so the email's
    // @media (max-width:600px) rules evaluate as mobile and the responsive
    // layout (stacked columns, scaled headings, fluid images) kicks in.
    document.getElementById('__preview-frame').style.width = mode === 'mobile' ? '390px' : '100%';
  }
<\/script>
</body>
</html>`;

      win.document.open();
      win.document.write(shell);
      win.document.close();
      win.document.title = rawTitle + " · Preview";

      // Write the compiled email into the iframe's own document.
      const frame = win.document.getElementById("__preview-frame");
      const fdoc  = frame.contentDocument || frame.contentWindow.document;
      fdoc.open();
      fdoc.write(html);
      fdoc.close();
    } catch (e) {
      win.close();
      toast.error("Preview failed: " + describeError(e));
    } finally {
      previewing.value = false;
    }
  }

  return { previewing, openPreview };
}
