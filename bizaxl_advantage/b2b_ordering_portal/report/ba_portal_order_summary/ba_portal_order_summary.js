// Copyright (c) 2026, Bizaxl and contributors
// For license information, please see license.txt

frappe.query_reports["BA Portal Order Summary"] = {
	filters: [
		{
			fieldname: "buyer",
			label: __("Buyer"),
			fieldtype: "Link",
			options: "BA Portal Buyer",
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nDraft\nSubmitted\nConfirmed\nDispatched\nInvoiced\nCompleted\nCancelled",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
	],
};
