// Intercept the Letters workspace and redirect to the Letter Builder Vue dashboard.
// The workspace controller lazily registers frappe.pages["letters"] after our
// app_include_js runs, so we use Object.defineProperty to intercept that write
// and inject our redirect into whatever page object it registers.
(function () {
  function install() {
    if (!window.frappe || !frappe.pages) {
      return setTimeout(install, 50);
    }

    var _page = frappe.pages["letters"];

    function applyRedirect(page) {
      if (page && typeof page === "object") {
        page.on_page_load = function () {
          frappe.set_route("letter-builder");
        };
        page.on_page_show = function () {
          frappe.set_route("letter-builder");
        };
      }
      return page;
    }

    Object.defineProperty(frappe.pages, "letters", {
      get: function () { return _page; },
      set: function (val) { _page = applyRedirect(val); },
      configurable: true,
    });

    // If workspace already registered before we ran
    if (_page) applyRedirect(_page);
  }

  install();
})();
