# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime


class BAPortalOrder(Document):
	def validate(self):
		self.calculate_totals()
		self.validate_stock_availability()

	def calculate_totals(self):
		total_qty = 0.0
		total_amount = 0.0
		for row in self.items:
			row.amount = flt(row.qty) * flt(row.rate)
			total_qty += flt(row.qty)
			total_amount += flt(row.amount)
		self.total_qty = total_qty
		self.total_amount = total_amount

	def validate_stock_availability(self):
		"""Soft-check requested qty against BA Stock Snapshot (synced from Bin).
		Flags rather than hard-blocks by default; see settings if you want a hard stop."""
		for row in self.items:
			available = frappe.db.get_value(
				"BA Stock Snapshot", {"item": row.item}, "available_qty"
			)
			if available is not None and flt(row.qty) > flt(available):
				frappe.msgprint(
					_("Requested qty for {0} ({1}) exceeds available stock ({2}).").format(
						row.item_name or row.item, row.qty, available
					),
					indicator="orange",
					alert=True,
				)

	def before_submit(self):
		if self.status == "Draft":
			self.status = "Submitted"

	def on_submit(self):
		self.add_status_log("Submitted")

	def on_cancel(self):
		self.add_status_log("Cancelled")

	def on_update_after_submit(self):
		self.add_status_log(self.status)

	def add_status_log(self, status):
		frappe.get_doc({
			"doctype": "BA Order Status Log",
			"portal_order": self.name,
			"status": status,
			"changed_on": now_datetime(),
		}).insert(ignore_permissions=True)

	def create_sales_order(self):
		"""Optional helper: convert this Portal Order into a real ERPNext Sales Order.
		Call explicitly (button / server script) rather than automatically on submit,
		so staff keep a manual confirmation step per the build plan."""
		if self.sales_order_ref:
			frappe.throw(_("Sales Order already created for this Portal Order."))

		buyer = frappe.get_doc("BA Portal Buyer", self.buyer)
		customer = frappe.db.get_value("Customer", {"customer_name": buyer.buyer_name})
		if not customer:
			frappe.throw(
				_("No ERPNext Customer record found for buyer {0}. Create/link one first.").format(
					buyer.buyer_name
				)
			)

		so = frappe.new_doc("Sales Order")
		so.customer = customer
		so.delivery_date = self.requested_delivery_date
		for row in self.items:
			so.append("items", {
				"item_code": row.item,
				"qty": row.qty,
				"rate": row.rate,
			})
		so.insert(ignore_permissions=True)
		self.db_set("sales_order_ref", so.name)
		return so.name
