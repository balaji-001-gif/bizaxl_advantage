# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt
"""
Shared helpers: portal permission-query conditions, and scheduled jobs
(stock snapshot sync, subscription expiry, usage counter reset).
Wired up via hooks.py (permission_query_conditions / scheduler_events).
"""

import frappe
from frappe.utils import add_days, flt, getdate, nowdate


# ---------------------------------------------------------------------------
# Permission query conditions
# ---------------------------------------------------------------------------

def _get_buyer_for_user(user):
	return frappe.db.get_value("BA Portal Buyer", {"portal_user": user}, "name")

def get_portal_order_permission_query(user):
	"""Restrict BA Portal Order list/report view so a logged-in buyer only
	ever sees their own orders -- mirrors the 'Customer' scoping used for
	the Web Form in the build plan (Phase 01 / 04 exit criteria)."""
	if not user:
		user = frappe.session.user
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return ""
	buyer = _get_buyer_for_user(user)
	if not buyer:
		return "1=0"
	return f"`tabBA Portal Order`.buyer = {frappe.db.escape(buyer)}"

def get_portal_buyer_permission_query(user):
	"""A buyer may only view their own BA Portal Buyer record."""
	if not user:
		user = frappe.session.user
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return ""
	buyer = _get_buyer_for_user(user)
	if not buyer:
		return "1=0"
	return f"`tabBA Portal Buyer`.name = {frappe.db.escape(buyer)}"

def get_visit_log_permission_query(user):
	"""A field rep only sees their own visit logs; managers (System Manager /
	Sales Manager) see everything."""
	if not user:
		user = frappe.session.user
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return ""
	rep = frappe.db.get_value("BA Field Rep", {"user": user}, "name")
	if not rep:
		return "1=0"
	return f"`tabBA Visit Log`.field_rep = {frappe.db.escape(rep)}"


def has_portal_order_permission(doc, ptype=None, user=None):
	"""Doc-level fallback for has_permission -- belt-and-braces alongside the
	list-level permission_query_conditions above."""
	user = user or frappe.session.user
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return True
	buyer = _get_buyer_for_user(user)
	return bool(buyer) and doc.buyer == buyer


def notify_manager_of_visit(doc, method=None):
	"""BA Visit Log after_insert: ping the field rep's manager (reports_to)
	with a system notification. Falls back to any Sales Manager if the rep
	has no manager set."""
	rep = frappe.get_doc("BA Field Rep", doc.field_rep)
	manager_user = None
	if rep.reports_to:
		manager_user = frappe.db.get_value("BA Field Rep", rep.reports_to, "user")

	recipients = [manager_user] if manager_user else frappe.get_all(
		"Has Role", filters={"role": "Sales Manager", "parenttype": "User"}, pluck="parent"
	)
	recipients = [r for r in recipients if r]
	if not recipients:
		return

	frappe.get_doc({
		"doctype": "Notification Log",
		"subject": f"{rep.rep_name} logged a visit to {doc.buyer}",
		"for_user": recipients[0],
		"type": "Alert",
		"document_type": "BA Visit Log",
		"document_name": doc.name,
	}).insert(ignore_permissions=True)


# ---------------------------------------------------------------------------
# Scheduled jobs
# ---------------------------------------------------------------------------

def sync_stock_snapshot():
	"""Hourly job: refresh BA Stock Snapshot from the live Bin table for every
	item flagged 'Show On Portal' in BA Portal Catalog Item. Keeps portal
	stock visibility live without duplicating the stock ledger (Phase 03)."""
	catalog_items = frappe.get_all(
		"BA Portal Catalog Item", filters={"show_on_portal": 1}, pluck="item"
	)
	if not catalog_items:
		return

	bins = frappe.get_all(
		"Bin",
		filters={"item_code": ["in", catalog_items]},
		fields=["item_code", "warehouse", "actual_qty", "reserved_qty"],
	)

	for b in bins:
		available = flt(b.actual_qty) - flt(b.reserved_qty)
		status = "Out of Stock"
		if available > 10:
			status = "In Stock"
		elif available > 0:
			status = "Low Stock"

		name = frappe.db.get_value(
			"BA Stock Snapshot", {"item": b.item_code, "warehouse": b.warehouse}, "name"
		)
		values = {
			"item": b.item_code,
			"warehouse": b.warehouse,
			"available_qty": available,
			"reserved_qty": b.reserved_qty,
			"stock_status": status,
			"last_synced": frappe.utils.now_datetime(),
		}
		if name:
			frappe.db.set_value("BA Stock Snapshot", name, values)
		else:
			frappe.get_doc({"doctype": "BA Stock Snapshot", **values}).insert(
				ignore_permissions=True
			)
	frappe.db.commit()


def check_subscription_expiry():
	"""Daily job: mark BA Buyer Subscription as Expired once end_date has
	passed. Reminder emails before expiry are handled by the shipped
	'Subscription Expiring Soon' Notification (Days Before end_date)."""
	expired = frappe.get_all(
		"BA Buyer Subscription",
		filters={"status": ["in", ["Active", "Trial"]], "end_date": ["<", nowdate()]},
		pluck="name",
	)
	for name in expired:
		frappe.db.set_value("BA Buyer Subscription", name, "status", "Expired")
	if expired:
		frappe.db.commit()


def reset_monthly_usage_counters():
	"""Monthly job: zero out usage counters whose period_start is >=30 days
	old, so tiered-plan limits (e.g. orders_this_month) roll over cleanly."""
	stale = frappe.get_all(
		"BA Usage Counter",
		filters={"period_start": ["<", add_days(nowdate(), -30)]},
		pluck="name",
	)
	for name in stale:
		frappe.db.set_value(
			"BA Usage Counter", name, {"count": 0, "period_start": nowdate()}
		)
	if stale:
		frappe.db.commit()
