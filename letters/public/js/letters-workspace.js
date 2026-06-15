// Redirect the Letters workspace to the Letter Builder dashboard view.
frappe.pages["letters"] = {
  on_page_load: function () {
    frappe.set_route("letter-builder");
  },
};
