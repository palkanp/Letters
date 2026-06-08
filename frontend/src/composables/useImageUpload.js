import { ref } from "vue";

/**
 * Reusable image-upload logic shared by every block that accepts an image.
 *
 * Encapsulates the Frappe `/api/method/upload_file` call (CSRF + error
 * unwrapping), drag-and-drop handling, and the file <input> ref so that
 * block components only deal with presentation.
 *
 * @param {(url: string) => void} onUploaded - called with the new file_url on success.
 * @returns upload state + handlers to bind in a template.
 */
export function useImageUpload(onUploaded) {
  const fileInput   = ref(null);
  const uploading   = ref(false);
  const uploadError = ref("");
  const isDragging  = ref(false);

  function triggerFileInput() {
    fileInput.value?.click();
  }

  function onFileSelect(e) {
    const file = e.target.files?.[0];
    if (file) uploadFile(file);
  }

  function onFileDrop(e) {
    isDragging.value = false;
    const file = e.dataTransfer?.files?.[0];
    if (file && file.type.startsWith("image/")) uploadFile(file);
  }

  async function uploadFile(file) {
    uploading.value   = true;
    uploadError.value = "";
    try {
      const fd = new FormData();
      fd.append("file", file, file.name);
      fd.append("is_private", "0");
      fd.append("doctype", "Email Campaign");

      // Frappe CSRF token — always available on window.frappe in Desk context
      const csrf = window?.frappe?.csrf_token || "";

      const res = await fetch("/api/method/upload_file", {
        method:  "POST",
        headers: { "X-Frappe-CSRF-Token": csrf, "Accept": "application/json" },
        body:    fd,
      });

      const data = await res.json();

      // Frappe wraps errors in exc / _server_messages even on HTTP 200
      if (data.exc || data._server_messages) {
        throw new Error("Upload rejected by server");
      }

      const url = data?.message?.file_url;
      if (!url) throw new Error("No file URL in response");

      onUploaded?.(url);
    } catch (err) {
      uploadError.value = err.message || "Upload failed";
    } finally {
      uploading.value = false;
      if (fileInput.value) fileInput.value.value = "";
    }
  }

  return {
    fileInput,
    uploading,
    uploadError,
    isDragging,
    triggerFileInput,
    onFileSelect,
    onFileDrop,
    uploadFile,
  };
}
