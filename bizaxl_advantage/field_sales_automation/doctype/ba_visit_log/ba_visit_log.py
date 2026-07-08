# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BAVisitLog(Document):
	def after_insert(self):
		self.mark_route_plan_visit_as_visited()

	def mark_route_plan_visit_as_visited(self):
		"""If today's BA Route Plan for this rep includes this buyer, flip that
		row to 'Visited' automatically so managers see live progress."""
		route_plan = frappe.db.get_value(
			"BA Route Plan",
			{"field_rep": self.field_rep, "plan_date": frappe.utils.getdate(self.visit_datetime)},
			"name",
		)
		if not route_plan:
			return
		rp = frappe.get_doc("BA Route Plan", route_plan)
		changed = False
		for row in rp.visits:
			if row.buyer == self.buyer and row.visit_status == "Pending":
				row.visit_status = "Visited"
				changed = True
		if changed:
			rp.save(ignore_permissions=True)
