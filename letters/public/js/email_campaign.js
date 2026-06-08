frappe.ui.form.on("Email Campaign", {
    refresh(frm) {
        frm.add_custom_button(__("Open in Letter Builder"), () => {
            const path = frm.is_new()
                ? "/letters-builder"
                : `/letters-builder?name=${encodeURIComponent(frm.doc.name)}`;
            window.open(path, "_blank");
        });
    },
});
