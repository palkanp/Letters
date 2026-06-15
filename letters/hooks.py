app_name = "letters"
app_title = "Letters"
app_publisher = "Palkan Parsana"
app_description = "Visual email design and campaign system for Frappe"
app_email = "palkan@frappe.io"
app_license = "MIT"

# Frappe version compatibility
required_apps = ["frappe"]

# DocTypes for which the app is the owner
# Included in standard_queries by default

# Background job queues used
scheduler_events = {
    "cron": {
        "*/5 * * * *": ["letters.letters.api.process_scheduled_sends"],
    }
}

# Jinja templates
# jinja = {
#     "methods": [],
#     "filters": [],
# }

# The Vite IIFE bundle inlines its CSS (injects a <style> tag at runtime),
# so there is no separate .css file to register via page_css.
page_js = {"letter-builder": "public/js/letter-builder.js"}

doctype_js = {"Letter": "public/frappe_customizations/email_campaign.js"}

fixtures = ["Letters Template"]

# Override standard DocType forms
# override_doctype_class = {}
