app_name = "letters"
app_title = "Letters"
app_publisher = "Palkan Parsana"
app_description = "Visual email design and campaign system for Frappe"
app_email = ""
app_license = "MIT"

# Frappe version compatibility
required_apps = ["frappe"]

# DocTypes for which the app is the owner
# Included in standard_queries by default

# Background job queues used
# scheduler_events = {
#     "cron": {
#         "*/5 * * * *": ["letters.tasks.process_scheduled_sends"],
#     }
# }

# Jinja templates
# jinja = {
#     "methods": [],
#     "filters": [],
# }

page_js = {"letters-builder": "public/js/letters-builder.js"}
page_css = {"letters-builder": "public/js/letters-builder.css"}

doctype_js = {"Email Campaign": "public/frappe_customizations/email_campaign.js"}

# Override standard DocType forms
# override_doctype_class = {}
