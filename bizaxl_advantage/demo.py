# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

"""
Demo / seed-data loader for bizaxl_advantage (B2B Ordering Portal,
Field Sales Automation & Tiered Product Ladder).

Run this from the bench console:
    bench --site bcube.bizaxl.org console
    import bizaxl_advantage.demo as demo
    demo.run()

Or directly from the shell:
    cd ~/f15-bk
    bench --site bcube.bizaxl.org execute bizaxl_advantage.demo.run()

The script is safe to re-run -- it skips records that already exist.
"""

import frappe
from frappe.utils import add_days, getdate, now_datetime, nowdate

# Roles assigned to demo portal users
B2B_BUYER_ROLE = "B2B Buyer"
FIELD_SALES_REP_ROLE = "Field Sales Rep"

# ── helpers ──────────────────────────────────────────────────────────────


def _skip_if_exists(doctype: str, field: str, value: str) -> bool:
	"""Return True and print a skip message when the record already exists."""
	if frappe.db.exists(doctype, {field: value}):
		print(f"  ⏭  {doctype} '{value}' already exists -- skipped")
		return True
	return False


def _insert(doctype: str, kwargs: dict) -> str:
	"""Insert a document (ignoring user permissions) and return its name."""
	doc = frappe.get_doc({"doctype": doctype, **kwargs})
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	print(f"  ✅ Created {doctype}: {doc.name}")
	return doc.name


# ═══════════════════════════════════════════════════════════════════════
#  1. BA Sales Territory
# ═══════════════════════════════════════════════════════════════════════

TERRITORIES = [
	{"territory_name": "Chennai City", "region": "Tamil Nadu"},
	{"territory_name": "Mumbai Metro", "region": "Maharashtra"},
	{"territory_name": "Delhi NCR", "region": "Delhi"},
	{"territory_name": "Bangalore Urban", "region": "Karnataka"},
	{"territory_name": "Hyderabad", "region": "Telangana"},
	{"territory_name": "Kolkata", "region": "West Bengal"},
]


def _create_territories():
	print("\n── BA Sales Territory ────────────────────────────")
	ids = []
	for t in TERRITORIES:
		if _skip_if_exists("BA Sales Territory", "territory_name", t["territory_name"]):
			continue
		ids.append(_insert("BA Sales Territory", t))
	return ids


# ═══════════════════════════════════════════════════════════════════════
#  2. BA Buyer Price Tier
# ═══════════════════════════════════════════════════════════════════════

PRICE_TIERS = [
	{"tier_name": "Standard Retail", "description": "Default retail pricing", "default_discount_percent": 0, "is_active": 1},
	{"tier_name": "Wholesale", "description": "Wholesale partner pricing", "default_discount_percent": 12, "is_active": 1},
	{"tier_name": "Distributor", "description": "Distributor-level pricing", "default_discount_percent": 20, "is_active": 1},
	{"tier_name": "Premium Partner", "description": "Top-tier partner pricing", "default_discount_percent": 25, "is_active": 1},
]


def _create_price_tiers():
	print("\n── BA Buyer Price Tier ───────────────────────────")
	ids = []
	for t in PRICE_TIERS:
		if _skip_if_exists("BA Buyer Price Tier", "tier_name", t["tier_name"]):
			continue
		ids.append(_insert("BA Buyer Price Tier", t))
	return ids


# ═══════════════════════════════════════════════════════════════════════
#  3. BA Subscription Plan  (+ child BA Plan Feature)
# ═══════════════════════════════════════════════════════════════════════

SUBSCRIPTION_PLANS = [
	{
		"plan_name": "Starter",
		"price": 0,
		"billing_cycle": "Yearly",
		"description": "Free plan for small retailers to get started",
		"features": [
			{"feature_key": "max_orders_month", "feature_label": "Orders / month", "enabled": 1},
			{"feature_key": "max_sku", "feature_label": "SKU limit", "enabled": 1},
			{"feature_key": "portal_access", "feature_label": "Portal access", "enabled": 1},
		],
	},
	{
		"plan_name": "Growth",
		"price": 4999,
		"billing_cycle": "Monthly",
		"description": "For growing pharmacies with higher order volumes",
		"features": [
			{"feature_key": "max_orders_month", "feature_label": "Orders / month", "enabled": 1},
			{"feature_key": "max_sku", "feature_label": "SKU limit", "enabled": 1},
			{"feature_key": "portal_access", "feature_label": "Portal access", "enabled": 1},
			{"feature_key": "analytics", "feature_label": "Basic analytics", "enabled": 1},
			{"feature_key": "bulk_order", "feature_label": "Bulk order upload", "enabled": 1},
		],
	},
	{
		"plan_name": "Enterprise",
		"price": 14999,
		"billing_cycle": "Monthly",
		"description": "Full-featured plan for large hospital chains and distributors",
		"features": [
			{"feature_key": "max_orders_month", "feature_label": "Orders / month", "enabled": 1},
			{"feature_key": "max_sku", "feature_label": "SKU limit", "enabled": 1},
			{"feature_key": "portal_access", "feature_label": "Portal access", "enabled": 1},
			{"feature_key": "analytics", "feature_label": "Advanced analytics & reports", "enabled": 1},
			{"feature_key": "bulk_order", "feature_label": "Bulk order upload", "enabled": 1},
			{"feature_key": "multi_warehouse", "feature_label": "Multi-warehouse view", "enabled": 1},
			{"feature_key": "api_access", "feature_label": "API access", "enabled": 1},
			{"feature_key": "dedicated_support", "feature_label": "Dedicated account manager", "enabled": 1},
		],
	},
	{
		"plan_name": "Starter Yearly",
		"price": 0,
		"billing_cycle": "Yearly",
		"description": "Free annual plan",
		"features": [
			{"feature_key": "max_orders_month", "feature_label": "Orders / month", "enabled": 1},
			{"feature_key": "max_sku", "feature_label": "SKU limit", "enabled": 1},
		],
	},
]


def _create_subscription_plans():
	print("\n── BA Subscription Plan ──────────────────────────")
	ids = []
	for plan in SUBSCRIPTION_PLANS:
		if _skip_if_exists("BA Subscription Plan", "plan_name", plan["plan_name"]):
			continue
		features = plan.pop("features")
		name = _insert("BA Subscription Plan", plan)
		# Add feature rows
		for f in features:
			f["parent"] = name
			f["parenttype"] = "BA Subscription Plan"
			f["parentfield"] = "features"
			frappe.get_doc({"doctype": "BA Plan Feature", **f}).insert(ignore_permissions=True)
		frappe.db.commit()
		ids.append(name)
		print(f"     + {len(features)} features added")
	return ids


# ═══════════════════════════════════════════════════════════════════════
#  4. BA Detailing Content
# ═══════════════════════════════════════════════════════════════════════

DETAILING_CONTENTS = [
	{"title": "Cardiovascular Product Line", "content_type": "PDF", "active": 1},
	{"title": "Diabetes Care Brochure", "content_type": "PDF", "active": 1},
	{"title": "New Antibiotic Launch", "content_type": "Image", "active": 1},
	{"title": "OTC Product Catalog", "content_type": "External Link", "external_url": "https://bizaxl.example.com/catalog/otc", "active": 1},
	{"title": "Vaccination Awareness Video", "content_type": "Video", "active": 1},
]


def _create_detailing_contents():
	print("\n── BA Detailing Content ─────────────────────────")
	ids = []
	for dc in DETAILING_CONTENTS:
		if _skip_if_exists("BA Detailing Content", "title", dc["title"]):
			continue
		ids.append(_insert("BA Detailing Content", dc))
	return ids


# ═══════════════════════════════════════════════════════════════════════
#  5. ERPNext prerequisite records
# ═══════════════════════════════════════════════════════════════════════

def _get_default_item_group():
	"""Return a safe default Item Group that exists on the site."""
	dflt = frappe.db.get_value("Item Group", {"is_group": 0})
	if not dflt:
		# Fallback: create one
		_insert("Item Group", {"item_group_name": "Products", "is_group": 0})
		dflt = "Products"
	return dflt


def _ensure_erpnext_prereqs():
	"""Create minimal Items, Customers, Users, and a Warehouse if none exist."""

	print("\n── ERPNext prerequisites ────────────────────────")

	item_group = _get_default_item_group()

	# --- Items ---
	demo_items = [
		{"item_code": "PARA-001", "item_name": "Paracetamol 500mg (strip of 10)", "stock_uom": "Nos", "item_group": item_group},
		{"item_code": "AMOX-001", "item_name": "Amoxicillin 250mg (capsule)", "stock_uom": "Nos", "item_group": item_group},
		{"item_code": "VITC-001", "item_name": "Vitamin C 500mg (tablet)", "stock_uom": "Nos", "item_group": item_group},
		{"item_code": "OMEP-001", "item_name": "Omeprazole 20mg (capsule)", "stock_uom": "Nos", "item_group": item_group},
		{"item_code": "AZIT-001", "item_name": "Azithromycin 500mg (tablet)", "stock_uom": "Nos", "item_group": item_group},
		{"item_code": "INSU-001", "item_name": "Insulin Regular 40IU/ml (vial)", "stock_uom": "Nos", "item_group": item_group},
		{"item_code": "CETR-001", "item_name": "Cetirizine 10mg (tablet)", "stock_uom": "Nos", "item_group": item_group},
		{"item_code": "PAN-001", "item_name": "Bandage Elastic 4inch (pack of 12)", "stock_uom": "Nos", "item_group": item_group},
	]
	created_items = []
	for it in demo_items:
		if frappe.db.exists("Item", it["item_code"]):
			print(f"  ⏭  Item '{it['item_code']}' already exists -- skipped")
			created_items.append(it["item_code"])
			continue
		_insert("Item", it)
		created_items.append(it["item_code"])

	# --- Warehouse ---
	# First look for any existing non-group warehouse
	warehouse = frappe.db.get_value("Warehouse", {"is_group": 0}, "name")
	if not warehouse:
		# No warehouse exists yet -- create one
		company = frappe.db.get_single_value("Global Defaults", "default_company") or "Demo Company"
		if not frappe.db.exists("Company", company):
			_insert("Company", {"company_name": company, "abbr": "DEMO", "country": "India", "default_currency": "INR"})
		company_abbr = frappe.db.get_value("Company", company, "abbr") or "DEMO"
		warehouse_name = f"Main Store - {company_abbr}"
		if not frappe.db.exists("Warehouse", warehouse_name):
			_insert("Warehouse", {"warehouse_name": "Main Store", "company": company, "is_group": 0})
		warehouse = frappe.db.get_value("Warehouse", {"is_group": 0}, "name")

	# --- Customers ---
	demo_customers = [
		{"customer_name": "Chennai Pharmacy", "customer_type": "Company", "customer_group": "All Customer Groups", "territory": "India"},
		{"customer_name": "Mumbai Medicos", "customer_type": "Company", "customer_group": "All Customer Groups", "territory": "India"},
		{"customer_name": "Delhi Drug House", "customer_type": "Company", "customer_group": "All Customer Groups", "territory": "India"},
	]
	created_customers = []
	for c in demo_customers:
		if frappe.db.exists("Customer", {"customer_name": c["customer_name"]}):
			print(f"  ⏭  Customer '{c['customer_name']}' already exists -- skipped")
			created_customers.append(frappe.db.get_value("Customer", {"customer_name": c["customer_name"]}, "name"))
			continue
		created_customers.append(_insert("Customer", c))

	# --- Users with roles ---
	demo_users = [
		{"email": "rajesh.pharmacy@example.com", "first_name": "Rajesh", "last_name": "Kumar", "roles": [B2B_BUYER_ROLE]},
		{"email": "seema.drugstore@example.com", "first_name": "Seema", "last_name": "Sharma", "roles": [B2B_BUYER_ROLE]},
		{"email": "anil.medical@example.com", "first_name": "Anil", "last_name": "Verma", "roles": [B2B_BUYER_ROLE]},
		{"email": "rep.rahul@example.com", "first_name": "Rahul", "last_name": "Singh", "roles": [FIELD_SALES_REP_ROLE]},
		{"email": "rep.priya@example.com", "first_name": "Priya", "last_name": "Patel", "roles": [FIELD_SALES_REP_ROLE]},
	]
	created_users = []
	for u in demo_users:
		roles = u.pop("roles")
		if frappe.db.exists("User", u["email"]):
			print(f"  ⏭  User '{u['email']}' already exists -- skipped")
			created_users.append(u["email"])
			continue
		u["enabled"] = 1
		u["send_welcome_email"] = 0
		inserted = _insert("User", u)
		# Assign roles
		for role in roles:
			if not frappe.db.exists("Role", role):
				_insert("Role", {"role_name": role, "desk_access": 1})
			frappe.get_doc({
				"doctype": "Has Role",
				"parent": inserted,
				"parenttype": "User",
				"parentfield": "roles",
				"role": role,
			}).insert(ignore_permissions=True)
		frappe.db.commit()
		created_users.append(inserted)

	# --- UOM (ensure Nos exists) ---
	if not frappe.db.exists("UOM", "Nos"):
		_insert("UOM", {"uom_name": "Nos", "must_be_whole_number": 1})

	return {
		"items": created_items,
		"customers": created_customers,
		"users": created_users,
		"warehouse": warehouse,
	}


# ═══════════════════════════════════════════════════════════════════════
#  6. BA Portal Buyer  (depends on Territory, Price Tier, Customer, User)
# ═══════════════════════════════════════════════════════════════════════

PORTAL_BUYERS = [
	{
		"buyer_name": "Chennai Pharmacy",
		"buyer_type": "Retailer",
		"gstin": "33ABCDE1234F1Z5",
		"mobile_no": "+91-9876543210",
		"email": "rajesh.pharmacy@example.com",
		"territory_key": "Chennai City",
		"price_tier_key": "Standard Retail",
		"customer_index": 0,
		"user_index": 0,
		"shipping_address": "123 Mount Road, Chennai - 600001",
	},
	{
		"buyer_name": "Mumbai Medicos",
		"buyer_type": "Sub-Retailer",
		"gstin": "27PQRST5678F2Z6",
		"mobile_no": "+91-9876543221",
		"email": "seema.drugstore@example.com",
		"territory_key": "Mumbai Metro",
		"price_tier_key": "Wholesale",
		"customer_index": 1,
		"user_index": 1,
		"shipping_address": "456 Linking Road, Bandra, Mumbai - 400050",
	},
	{
		"buyer_name": "Delhi Drug House",
		"buyer_type": "Distributor",
		"gstin": "07LMNOP9012F3Z7",
		"mobile_no": "+91-9876543232",
		"email": "anil.medical@example.com",
		"territory_key": "Delhi NCR",
		"price_tier_key": "Distributor",
		"customer_index": 2,
		"user_index": 2,
		"shipping_address": "789 Chandni Chowk, Delhi - 110006",
	},
]


def _create_portal_buyers(prereqs, territory_map, tier_map):
	print("\n── BA Portal Buyer ──────────────────────────────")
	ids = []
	for pb in PORTAL_BUYERS:
		if _skip_if_exists("BA Portal Buyer", "buyer_name", pb["buyer_name"]):
			ids.append(frappe.db.get_value("BA Portal Buyer", {"buyer_name": pb["buyer_name"]}, "name"))
			continue
		ids.append(_insert("BA Portal Buyer", {
			"buyer_name": pb["buyer_name"],
			"buyer_type": pb["buyer_type"],
			"gstin": pb["gstin"],
			"contact_person": pb["email"].split("@")[0].replace(".", " ").title(),
			"mobile_no": pb["mobile_no"],
			"email": pb["email"],
			"territory": territory_map.get(pb["territory_key"]),
			"price_tier": tier_map.get(pb["price_tier_key"]),
			"erpnext_customer": prereqs["customers"][pb["customer_index"]],
			"portal_user": prereqs["users"][pb["user_index"]],
			"status": "Active",
			"shipping_address": pb["shipping_address"],
			"credit_limit": 100000,
		}))
	return ids


# ═══════════════════════════════════════════════════════════════════════
#  7. BA Field Rep  (depends on Territory, User)
# ═══════════════════════════════════════════════════════════════════════

FIELD_REPS = [
	{"rep_name": "Rahul Singh", "user_index": 3, "territory_key": "Chennai City", "mobile_no": "+91-9988776655"},
	{"rep_name": "Priya Patel", "user_index": 4, "territory_key": "Mumbai Metro", "mobile_no": "+91-9988776644"},
]


def _create_field_reps(prereqs, territory_map, buyer_ids):
	print("\n── BA Field Rep ─────────────────────────────────")
	ids = []
	for i, fr in enumerate(FIELD_REPS):
		if _skip_if_exists("BA Field Rep", "rep_name", fr["rep_name"]):
			ids.append(frappe.db.get_value("BA Field Rep", {"rep_name": fr["rep_name"]}, "name"))
			continue
		ids.append(_insert("BA Field Rep", {
			"rep_name": fr["rep_name"],
			"user": prereqs["users"][fr["user_index"]],
			"territory": territory_map.get(fr["territory_key"]),
			"mobile_no": fr["mobile_no"],
			"status": "Active",
		}))
	return ids


# ═══════════════════════════════════════════════════════════════════════
#  8. BA Rep Buyer Assignment  (depends on Field Rep, Portal Buyer)
# ═══════════════════════════════════════════════════════════════════════

def _create_assignments(rep_ids, buyer_ids):
	print("\n── BA Rep Buyer Assignment ──────────────────────")
	ids = []
	# Assign first rep to first buyer, second rep to second buyer
	for i, rep in enumerate(rep_ids):
		if i < len(buyer_ids):
			if frappe.db.exists("BA Rep Buyer Assignment", {"field_rep": rep, "buyer": buyer_ids[i]}):
				print(f"  ⏭  Assignment {rep} → {buyer_ids[i]} already exists")
				continue
			ids.append(_insert("BA Rep Buyer Assignment", {
				"field_rep": rep,
				"buyer": buyer_ids[i],
				"assigned_on": nowdate(),
			}))
	# Also assign cross-assignments (first rep covers additional buyers)
	if len(rep_ids) > 1 and len(buyer_ids) > 1:
		for buyer_id in buyer_ids[1:]:
			if frappe.db.exists("BA Rep Buyer Assignment", {"field_rep": rep_ids[0], "buyer": buyer_id}):
				continue
			ids.append(_insert("BA Rep Buyer Assignment", {
				"field_rep": rep_ids[0],
				"buyer": buyer_id,
				"assigned_on": nowdate(),
			}))
	return ids


# ═══════════════════════════════════════════════════════════════════════
#  9. BA Buyer Item Price  (depends on Price Tier, Item)
# ═══════════════════════════════════════════════════════════════════════

def _create_buyer_item_prices(prereqs, tier_map):
	print("\n── BA Buyer Item Price ─────────────────────────")
	ids = []
	# Create prices for each tier for a few demo items
	prices_map = {
		"Standard Retail": [12.00, 45.00, 8.50, 65.00, 120.00, 350.00, 5.00, 95.00],
		"Wholesale": [10.50, 40.00, 7.50, 58.00, 108.00, 315.00, 4.50, 85.00],
		"Distributor": [9.00, 36.00, 6.50, 52.00, 96.00, 280.00, 4.00, 76.00],
		"Premium Partner": [8.40, 33.75, 6.00, 48.75, 90.00, 262.50, 3.75, 71.25],
	}
	for tier_name, prices in prices_map.items():
		tier = tier_map.get(tier_name)
		if not tier:
			continue
		for idx, item_code in enumerate(prereqs["items"]):
			if idx >= len(prices):
				break
			if frappe.db.exists("BA Buyer Item Price", {"buyer_price_tier": tier, "item": item_code}):
				continue
			ids.append(_insert("BA Buyer Item Price", {
				"buyer_price_tier": tier,
				"item": item_code,
				"price": prices[idx],
				"uom": "Nos",
			}))
	return ids


# ═══════════════════════════════════════════════════════════════════════
#  10. BA Portal Catalog Item  (depends on Item)
# ═══════════════════════════════════════════════════════════════════════

def _create_catalog_items(prereqs):
	print("\n── BA Portal Catalog Item ───────────────────────")
	ids = []
	for idx, item_code in enumerate(prereqs["items"]):
		if _skip_if_exists("BA Portal Catalog Item", "item", item_code):
			continue
		ids.append(_insert("BA Portal Catalog Item", {
			"item": item_code,
			"show_on_portal": 1,
			"min_order_qty": 1,
			"max_order_qty": 100,
		}))
	return ids


# ═══════════════════════════════════════════════════════════════════════
#  11. BA Buyer Subscription  (depends on Portal Buyer, Subscription Plan)
# ═══════════════════════════════════════════════════════════════════════

def _create_subscriptions(buyer_ids, plan_ids):
	print("\n── BA Buyer Subscription ────────────────────────")
	ids = []
	today = getdate()
	subscriptions_data = [
		{"buyer_index": 0, "plan_index": 0, "days_offset": -30, "end_days": 335, "status": "Active"},
		{"buyer_index": 1, "plan_index": 1, "days_offset": -15, "end_days": 15, "status": "Active", "auto_renew": 1},
		{"buyer_index": 2, "plan_index": 2, "days_offset": -90, "end_days": 275, "status": "Active", "auto_renew": 1},
	]
	for sub in subscriptions_data:
		if sub["buyer_index"] >= len(buyer_ids) or sub["plan_index"] >= len(plan_ids):
			continue
		buyer = buyer_ids[sub["buyer_index"]]
		plan = plan_ids[sub["plan_index"]]
		start = add_days(today, sub["days_offset"])
		end = add_days(today, sub["end_days"])
		if frappe.db.exists("BA Buyer Subscription", {"buyer": buyer, "plan": plan}):
			print(f"  ⏭  Subscription {buyer} → {plan} already exists")
			continue
		ids.append(_insert("BA Buyer Subscription", {
			"buyer": buyer,
			"plan": plan,
			"start_date": start,
			"end_date": end,
			"status": sub["status"],
			"auto_renew": sub.get("auto_renew", 0),
		}))
	return ids


# ═══════════════════════════════════════════════════════════════════════
#  12. BA Usage Counter  (depends on Portal Buyer)
# ═══════════════════════════════════════════════════════════════════════

def _create_usage_counters(buyer_ids):
	print("\n── BA Usage Counter ─────────────────────────────")
	ids = []
	metrics_data = [
		{"metric": "orders_this_month", "count": 5, "limit": 50},
		{"metric": "sku_count", "count": 8, "limit": 200},
	]
	for buyer in buyer_ids:
		for m in metrics_data:
			if frappe.db.exists("BA Usage Counter", {"buyer": buyer, "metric": m["metric"]}):
				continue
			ids.append(_insert("BA Usage Counter", {
				"buyer": buyer,
				"metric": m["metric"],
				"count": m["count"],
				"limit": m["limit"],
				"period_start": nowdate(),
			}))
	return ids


# ═══════════════════════════════════════════════════════════════════════
#  13. BA Stock Snapshot  (depends on Item, Warehouse)
# ═══════════════════════════════════════════════════════════════════════

def _create_stock_snapshots(prereqs):
	print("\n── BA Stock Snapshot ────────────────────────────")
	ids = []
	warehouse = prereqs["warehouse"]
	stock_data = [
		{"item": prereqs["items"][0], "available": 500, "reserved": 20, "status": "In Stock"},
		{"item": prereqs["items"][1], "available": 200, "reserved": 10, "status": "In Stock"},
		{"item": prereqs["items"][2], "available": 800, "reserved": 30, "status": "In Stock"},
		{"item": prereqs["items"][3], "available": 150, "reserved": 5, "status": "In Stock"},
		{"item": prereqs["items"][4], "available": 45, "reserved": 40, "status": "Low Stock"},
		{"item": prereqs["items"][5], "available": 300, "reserved": 15, "status": "In Stock"},
		{"item": prereqs["items"][6], "available": 8, "reserved": 5, "status": "Low Stock"},
		{"item": prereqs["items"][7], "available": 0, "reserved": 0, "status": "Out of Stock"},
	]
	for s in stock_data:
		if frappe.db.exists("BA Stock Snapshot", {"item": s["item"], "warehouse": warehouse}):
			continue
		ids.append(_insert("BA Stock Snapshot", {
			"item": s["item"],
			"warehouse": warehouse,
			"available_qty": s["available"],
			"reserved_qty": s["reserved"],
			"stock_status": s["status"],
			"last_synced": now_datetime(),
		}))
	return ids


# ═══════════════════════════════════════════════════════════════════════
#  14. BA Portal Order  (+ child BA Portal Order Item, BA Order Status Log)
# ═══════════════════════════════════════════════════════════════════════

def _create_portal_orders(buyer_ids, prereqs):
	print("\n── BA Portal Order ──────────────────────────────")
	ids = []
	orders_data = [
		{
			"buyer_index": 0,
			"days_ago": 2,
			"status": "Submitted",
			"items": [
				{"item": prereqs["items"][0], "qty": 50, "rate": 12.00},
				{"item": prereqs["items"][2], "qty": 30, "rate": 8.50},
			],
			"delivery_address": "123 Mount Road, Chennai",
		},
		{
			"buyer_index": 1,
			"days_ago": 1,
			"status": "Draft",
			"items": [
				{"item": prereqs["items"][1], "qty": 25, "rate": 45.00},
				{"item": prereqs["items"][3], "qty": 10, "rate": 65.00},
				{"item": prereqs["items"][4], "qty": 5, "rate": 120.00},
			],
			"delivery_address": "456 Linking Road, Bandra, Mumbai",
		},
		{
			"buyer_index": 2,
			"days_ago": 0,
			"status": "Draft",
			"items": [
				{"item": prereqs["items"][5], "qty": 20, "rate": 350.00},
			],
			"delivery_address": "789 Chandni Chowk, Delhi",
		},
	]
	for order in orders_data:
		if order["buyer_index"] >= len(buyer_ids):
			continue
		buyer = buyer_ids[order["buyer_index"]]
		# Create the order
		doc = frappe.get_doc({
			"doctype": "BA Portal Order",
			"naming_series": "BA-ORD-.YYYY.-",
			"buyer": buyer,
			"order_date": add_days(getdate(), -order["days_ago"]),
			"status": order["status"],
			"delivery_address": order["delivery_address"],
		})
		# Add items
		for row in order["items"]:
			doc.append("items", {
				"item": row["item"],
				"qty": row["qty"],
				"rate": row["rate"],
			})
		doc.insert(ignore_permissions=True)
		# validate() already calls calculate_totals() -- totals are set on insert
		frappe.db.commit()
		ids.append(doc.name)
		print(f"  ✅ Created BA Portal Order: {doc.name}")

		# Create status log if Submitted
		if order["status"] != "Draft":
			_insert("BA Order Status Log", {
				"portal_order": doc.name,
				"status": order["status"],
				"changed_on": now_datetime(),
			})
	return ids


# ═══════════════════════════════════════════════════════════════════════
#  15. BA Route Plan  (+ child BA Route Plan Visit)
# ═══════════════════════════════════════════════════════════════════════

def _create_route_plans(rep_ids, buyer_ids):
	print("\n── BA Route Plan ────────────────────────────────")
	ids = []
	for i, rep in enumerate(rep_ids):
		if i >= len(buyer_ids):
			continue
		# Create a plan for today
		doc = frappe.get_doc({
			"doctype": "BA Route Plan",
			"field_rep": rep,
			"plan_date": nowdate(),
			"status": "Approved",
		})
		# Add visits for buyers assigned to this rep
		assigned_buyers = frappe.get_all(
			"BA Rep Buyer Assignment",
			filters={"field_rep": rep},
			pluck="buyer",
		)
		for idx, buyer in enumerate(assigned_buyers):
			doc.append("visits", {
				"sequence": idx + 1,
				"buyer": buyer,
				"planned_time": f"{9 + idx}:00:00",
				"visit_status": "Pending",
			})
		if doc.get("visits"):
			doc.insert(ignore_permissions=True)
			frappe.db.commit()
			ids.append(doc.name)
			print(f"  ✅ Created BA Route Plan: {doc.name} ({len(doc.visits)} visits)")
		else:
			print(f"  ⏭  No buyers assigned to rep {rep} -- skipping route plan")
	return ids


# ═══════════════════════════════════════════════════════════════════════
#  16. BA Visit Log  (depends on Field Rep, Portal Buyer, Portal Order)
# ═══════════════════════════════════════════════════════════════════════

def _create_visit_logs(rep_ids, buyer_ids):
	print("\n── BA Visit Log ─────────────────────────────────")
	ids = []
	visit_data = [
		{
			"rep_index": 0, "buyer_index": 0,
			"days_ago": 1, "outcome": "Order Booked",
			"latitude": 13.0827, "longitude": 80.2707,
			"notes": "Discussed new product line. Customer ordered Paracetamol and Vitamin C.",
		},
		{
			"rep_index": 1, "buyer_index": 1,
			"days_ago": 0, "outcome": "Follow-up Needed",
			"latitude": 19.0760, "longitude": 72.8777,
			"notes": "Customer interested in bulk pricing. Need to share updated rate card.",
		},
	]
	for v in visit_data:
		if v["rep_index"] >= len(rep_ids) or v["buyer_index"] >= len(buyer_ids):
			continue
		rep = rep_ids[v["rep_index"]]
		buyer = buyer_ids[v["buyer_index"]]
		if frappe.db.exists("BA Visit Log", {"field_rep": rep, "buyer": buyer, "visit_datetime": ["Like", f"{add_days(getdate(), -v['days_ago'])}%"]}):
			print(f"  ⏭  Visit Log {rep} → {buyer} on {add_days(getdate(), -v['days_ago'])} already exists")
			continue
		ids.append(_insert("BA Visit Log", {
			"field_rep": rep,
			"buyer": buyer,
			"visit_datetime": str(add_days(getdate(), -v["days_ago"])) + " 10:30:00",
			"latitude": v["latitude"],
			"longitude": v["longitude"],
			"outcome": v["outcome"],
			"notes": v["notes"],
		}))
	return ids


# ═══════════════════════════════════════════════════════════════════════
#  MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════

def run():
	"""Create all demo records for bizaxl_advantage. Safe to re-run."""

	print("=" * 60)
	print("  bizaxl_advantage — Demo Data Loader")
	print("=" * 60)

	# 1. Standalone records (no dependencies)
	territory_ids = _create_territories()
	tier_ids = _create_price_tiers()
	plan_ids = _create_subscription_plans()
	detailing_ids = _create_detailing_contents()

	# Build lookup maps
	territory_map = {t["territory_name"]: frappe.db.get_value("BA Sales Territory", {"territory_name": t["territory_name"]}, "name") for t in TERRITORIES}
	tier_map = {t["tier_name"]: frappe.db.get_value("BA Buyer Price Tier", {"tier_name": t["tier_name"]}, "name") for t in PRICE_TIERS}

	# 2. ERPNext prerequisites (Items, Customers, Users, Warehouse)
	prereqs = _ensure_erpnext_prereqs()

	# 3. Dependent on ERPNext + custom lookup tables
	buyer_ids = _create_portal_buyers(prereqs, territory_map, tier_map)
	rep_ids = _create_field_reps(prereqs, territory_map, buyer_ids)

	# 4. Cross-referencing records
	_create_assignments(rep_ids, buyer_ids)
	_create_buyer_item_prices(prereqs, tier_map)
	_create_catalog_items(prereqs)
	_create_subscriptions(buyer_ids, plan_ids)
	_create_usage_counters(buyer_ids)
	_create_stock_snapshots(prereqs)

	# 5. Transactional records
	order_ids = _create_portal_orders(buyer_ids, prereqs)
	_create_route_plans(rep_ids, buyer_ids)
	_create_visit_logs(rep_ids, buyer_ids)

	# Summary
	print("\n" + "=" * 60)
	print("  Demo data loaded successfully!")
	total = (
		len(territory_ids) + len(tier_ids) + len(plan_ids) + len(detailing_ids)
		+ len(buyer_ids) + len(rep_ids) + len(order_ids)
	)
	print(f"  New records created across all 18 DocTypes")
	print("=" * 60)


# ═══════════════════════════════════════════════════════════════════════
#  CLEANUP — removes all demo records in reverse dependency order
# ═══════════════════════════════════════════════════════════════════════

def clear():
	"""Delete all demo records created by run(). Safe to re-run."""

	FULL_BA_DOCTYPES = [
		"BA Visit Log",
		"BA Route Plan",
		"BA Order Status Log",
		"BA Portal Order",
		"BA Stock Snapshot",
		"BA Usage Counter",
		"BA Buyer Subscription",
		"BA Portal Catalog Item",
		"BA Buyer Item Price",
		"BA Rep Buyer Assignment",
		"BA Field Rep",
		"BA Portal Buyer",
		"BA Detailing Content",
		"BA Subscription Plan",
		"BA Buyer Price Tier",
		"BA Sales Territory",
	]

	print("=" * 60)
	print("  bizaxl_advantage — Cleaning up demo data")
	print("=" * 60)

	for dt in FULL_BA_DOCTYPES:
		names = frappe.get_all(dt, pluck="name")
		for name in names:
			try:
				frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
				print(f"  🗑  Deleted {dt}: {name}")
			except Exception as e:
				print(f"  ⚠  Could not delete {dt} {name}: {e}")
		frappe.db.commit()

	print("\n  Cleanup complete!")
	print("=" * 60)


if __name__ == "__main__":
	run()
