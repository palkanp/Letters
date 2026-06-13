frappe.ui.form.on("Letters Campaign", {
    refresh(frm) {
        // Only offer the builder for a saved campaign. On a brand-new, unsaved
        // form we don't surface any builder/template entry point — campaigns are
        // meant to be started via "New Campaign" (which opens the picker).
        if (frm.is_new()) return;
        frm.add_custom_button(__("Open in Letters Builder"), () => {
            window.open(
                `/app/letters-builder?name=${encodeURIComponent(frm.doc.name)}`,
                "_blank"
            );
        });
    },
});

// Override the list view "New" button to go straight to the builder
// (which shows the template picker instead of the blank Frappe form).
frappe.listview_settings["Letters Campaign"] = {
    onload(listview) {
        listview.page.set_primary_action(__("New Campaign"), () => {
            window.open("/app/letters-builder", "_blank");
        }, "plus");
    },
};
