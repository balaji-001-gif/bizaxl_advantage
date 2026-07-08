app_name = "bizaxl_advantage"
app_title = "Bizaxl Advantage Suite"
app_publisher = "Bizaxl"
app_description = "B2B Ordering Portal, Field Sales Automation and Tiered Product Ladder for bizaxl Medical Retail on ERPNext v15+."
app_email = "dev@bizaxl.example"
app_license = "MIT"
required_apps = ["frappe/erpnext"]

# Fixtures shipped with the app: Workspace, Notification, Role, Web Form.
# `bench --site <site> export-fixtures` will re-export any edits you make
# in the desk back into these same files.
fixtures = [
	{"dt": "Workspace", "filters": [["name", "in", ["Bizaxl Advantage"]]]},
	{"dt": "Notification", "filters": [["name", "like", "BA %"]]},
	{"dt": "Role", "filters": [["name", "in", ["B2B Buyer", "Field Sales Rep"]]]},
	{"dt": "Web Form", "filters": [["name", "in", ["b2b-order"]]]},
]

# ---------------------------------------------------------------------------
# Document events
# ---------------------------------------------------------------------------
doc_events = {
	"BA Visit Log": {
		"after_insert": "bizaxl_advantage.utils.notify_manager_of_visit",
	},
}

# ---------------------------------------------------------------------------
# Permission query conditions -- scope portal/rep users to their own records
# ---------------------------------------------------------------------------
permission_query_conditions = {
	"BA Portal Order": "bizaxl_advantage.utils.get_portal_order_permission_query",
	"BA Portal Buyer": "bizaxl_advantage.utils.get_portal_buyer_permission_query",
	"BA Visit Log": "bizaxl_advantage.utils.get_visit_log_permission_query",
}

has_permission = {
	"BA Portal Order": "bizaxl_advantage.utils.has_portal_order_permission",
}

# ---------------------------------------------------------------------------
# Scheduled jobs
# ---------------------------------------------------------------------------
scheduler_events = {
	"hourly": [
		"bizaxl_advantage.utils.sync_stock_snapshot",
	],
	"daily": [
		"bizaxl_advantage.utils.check_subscription_expiry",
	],
	"monthly": [
		"bizaxl_advantage.utils.reset_monthly_usage_counters",
	],
}

# ---------------------------------------------------------------------------
# Website route rules (portal order Web Form is shipped as a fixture, but the
# route rule below is what actually exposes /b2b-order to logged-in buyers)
# ---------------------------------------------------------------------------
website_route_rules = [
	{"from_route": "/b2b-order", "to_route": "b2b-order"},
]
