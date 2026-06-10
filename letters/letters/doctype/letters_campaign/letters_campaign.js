// Client-side hooks for the Letters Campaign doctype.
// Adds a "Duplicate" action on the standard list view so users can
// copy a campaign without opening the builder first.

frappe.listview_settings["Letters Campaign"] = {
  add_fields: ["status", "subject"],

  get_indicator(doc) {
    const map = {
      Draft:    ["grey",   "status,=,Draft"],
      Ready:    ["green",  "status,=,Ready"],
      Sending:  ["orange", "status,=,Sending"],
      Failed:   ["red",    "status,=,Failed"],
    };
    return map[doc.status] || ["grey", "status,=,Draft"];
  },

  button: {
    show(doc) { return true; },
    get_label() { return __("Open"); },
    get_description(doc) { return __("Open in Letters builder"); },
    action(doc) {
      window.open(`/app/letters-builder?name=${encodeURIComponent(doc.name)}`, "_self");
    },
  },

  onload(listview) {
    listview.page.add_action_item(__("Duplicate"), async () => {
      const selected = listview.get_checked_items();
      if (!selected.length) {
        frappe.msgprint(__("Select at least one campaign to duplicate."));
        return;
      }

      frappe.confirm(
        __("Duplicate {0} campaign(s)?", [selected.length]),
        async () => {
          let done = 0;
          for (const row of selected) {
            try {
              await frappe.call({
                method: "letters.letters.api.duplicate_campaign",
                args: { name: row.name },
              });
              done++;
            } catch (e) {
              frappe.msgprint(__("Failed to duplicate {0}", [row.name]));
            }
          }
          frappe.show_alert({ message: __("{0} campaign(s) duplicated.", [done]), indicator: "green" });
          listview.refresh();
        }
      );
    });
  },
};
