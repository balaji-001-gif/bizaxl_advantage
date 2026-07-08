# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": _("Order"), "fieldname": "name", "fieldtype": "Link",
		 "options": "BA Portal Order", "width": 140},
		{"label": _("Buyer"), "fieldname": "buyer", "fieldtype": "Link",
		 "options": "BA Portal Buyer", "width": 180},
		{"label": _("Order Date"), "fieldname": "order_date", "fieldtype": "Date", "width": 100},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
		{"label": _("Total Qty"), "fieldname": "total_qty", "fieldtype": "Float", "width": 100},
		{"label": _("Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "width": 130},
		{"label": _("Sales Order"), "fieldname": "sales_order_ref", "fieldtype": "Link",
		 "options": "Sales Order", "width": 140},
	]


def get_data(filters):
	conditions = ["docstatus < 2"]
	values = {}

	if filters.get("buyer"):
		conditions.append("buyer = %(buyer)s")
		values["buyer"] = filters["buyer"]
	if filters.get("status"):
		conditions.append("status = %(status)s")
		values["status"] = filters["status"]
	if filters.get("from_date"):
		conditions.append("order_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("order_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	where = " and ".join(conditions)
	return frappe.db.sql(f"""
		select name, buyer, order_date, status, total_qty, total_amount, sales_order_ref
		from `tabBA Portal Order`
		where {where}
		order by order_date desc
	""", values, as_dict=1)
