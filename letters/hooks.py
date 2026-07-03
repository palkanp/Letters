app_name = "letters"
app_title = "Letters"
app_publisher = "Palkan Parsana"
app_description = "Visual email design and letter sending system for Frappe"
app_email = "palkan@frappe.io"
app_license = "AGPL-3.0"

# Frappe version compatibility
required_apps = ["frappe"]

# DocTypes for which the app is the owner
# Included in standard_queries by default

# Background job queues used
scheduler_events = {
    "cron": {
        "*/5 * * * *": [
            "letters.letters.api.process_scheduled_sends",
            "letters.letters.api.reconcile_active_sends",
        ],
    }
}

# Jinja templates
# jinja = {
#     "methods": [],
#     "filters": [],
# }

page_js = {"letter-builder": "public/js/letter-builder.js"}

doctype_js = {
    "Letter": "public/frappe_customizations/letter.js",
    "Notification": "public/frappe_customizations/notification.js",
}

fixtures = ["Letters Template"]

after_install = "letters.install.after_install"
after_migrate = "letters.install.after_migrate"

override_doctype_class = {
    "Notification": "letters.letters.overrides.notification.LettersNotification",
}

permission_query_conditions = {
    "Letter": "letters.letters.doctype.letter.letter.get_permission_query_conditions",
}
