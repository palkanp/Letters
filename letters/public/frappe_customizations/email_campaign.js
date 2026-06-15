frappe.ui.form.on("Letter", {
    refresh(frm) {
        // Builder entry point (restored): available on new and saved campaigns.
        frm.add_custom_button(__("Open in Letters Builder"), () => {
            const path = frm.is_new()
                ? "/app/letter-builder"
                : `/app/letter-builder?name=${encodeURIComponent(frm.doc.name)}`;
            window.open(path, "_blank");
        });

        // Remove Frappe's built-in form "Templates" feature on this DocType — it's
        // unrelated to Letters' own template system and only adds confusion here.
        // The native control is a top-bar button for new docs and a three-dot menu
        // item for saved docs; strip both. Deferred so the toolbar has rendered.
        setTimeout(() => {
            const tm = frm.toolbar && frm.toolbar.template_manager;
            if (tm && tm.$btn) tm.$btn.remove();
            frm.page.wrapper
                .find(".menu-btn-group .dropdown-item, .page-actions .dropdown-item")
                .filter((_, el) => el.textContent.trim() === __("Templates"))
                .remove();
        }, 0);
    },
});

// Override the list view "New" button to go straight to the builder
// (which shows the template picker instead of the blank Frappe form).
frappe.listview_settings["Letter"] = {
    onload(listview) {
        listview.page.set_primary_action(__("New Campaign"), () => {
            window.open("/app/letter-builder", "_blank");
        }, "plus");
    },
};
