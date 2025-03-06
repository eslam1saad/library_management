app_name = "library_management"
app_title = "Library Management"
app_publisher = "eslam attia"
app_description = "josoor test"
app_email = "eslam.attia2000@gmail.com"
app_license = "MIT"

# Include JavaScript and CSS files
app_include_js = "/assets/library_management/scripts.js"
app_include_css = "/assets/library_management/styles.css"
web_include_js = "/assets/frappe/js/frappe-web.min.js"
web_include_css = "/assets/frappe/css/frappe-web.css"

# ✅ Correctly overriding whitelisted methods
override_whitelisted_methods = {
    "frappe.csrf.get_token": "library_management.api.get_csrf_token"
}

# ✅ Whitelisting methods properly
whitelisted_methods = [
    "frappe.auth.get_logged_user",
    "frappe.csrf.get_token",
    "library_management.api.get_csrf_token",
    "library_management.api.get_books",
    "library_management.api.add_book",
    "library_management.api.delete_book",
    "library_management.api.delete_member",
    "library_management.api.issue_book",
    "library_management.api.return_book"
]


# ✅ CSRF Configuration (Secure Fix)
csrf = {"methods": ["POST"], "url": "/api/method/library_management.api.*"}

# ✅ CSRF Exemptions (ONLY IF NECESSARY)
csrf_exempt = [
    "library_management.api.add_book",
    "library_management.api.delete_book",
]

# ✅ API Methods (Correcting Structure)
api = {
    "methods": [
        {"method": "library_management.api.get_books", "type": "GET"},
        {"method": "library_management.api.add_book", "type": "POST"},
        {"method": "library_management.api.delete_book", "type": "POST"}
    ]
}
