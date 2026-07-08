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
		{"label": _("Field Rep"), "fieldname": "field_rep", "fieldtype": "Link",
		 "options": "BA Field Rep", "width": 160},
		{"label": _("Plan Date"), "fieldname": "plan_date", "fieldtype": "Date", "width": 100},
		{"label": _("Planned Visits"), "fieldname": "planned", "fieldtype": "Int", "width": 110},
		{"label": _("Completed Visits"), "fieldname": "visited", "fieldtype": "Int", "width": 120},
		{"label": _("Skipped"), "fieldname": "skipped", "fieldtype": "Int", "width": 90},
		{"label": _("Compliance %"), "fieldname": "compliance", "fieldtype": "Percent", "width": 110},
	]


def get_data(filters):
	conditions = ["rp.docstatus < 2"]
	values = {}
	if filters.get("field_rep"):
		conditions.append("rp.field_rep = %(field_rep)s")
		values["field_rep"] = filters["field_rep"]
	if filters.get("from_date"):
		conditions.append("rp.plan_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("rp.plan_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]
	where = " and ".join(conditions)

	plans = frappe.db.sql(f"""
		select rp.name, rp.field_rep, rp.plan_date
		from `tabBA Route Plan` rp
		where {where}
		order by rp.plan_date desc
	""", values, as_dict=1)

	rows = []
	for p in plans:
		visits = frappe.get_all(
			"BA Route Plan Visit",
			filters={"parent": p.name},
			fields=["visit_status"],
		)
		planned = len(visits)
		visited = len([v for v in visits if v.visit_status == "Visited"])
		skipped = len([v for v in visits if v.visit_status == "Skipped"])
		compliance = round((visited / planned) * 100, 1) if planned else 0
		rows.append({
			"field_rep": p.field_rep,
			"plan_date": p.plan_date,
			"planned": planned,
			"visited": visited,
			"skipped": skipped,
			"compliance": compliance,
		})
	return rows
