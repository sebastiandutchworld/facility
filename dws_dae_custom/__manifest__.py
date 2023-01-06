# Copyright 2015 ABF OSIELL <https://osiell.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# noinspection PyStatementEffect
{
    "name": "Customizations for Gearboks",
    "version": "13.0.1.0.1",
    "author": "Dutchworld Solutions",
    "license": "AGPL-3",
    "website": "https://dutchworld.nl",
    "category": "Tools",
    'description': """
    Various customizations
    Double analytic line protection Ticket #1822
    """,
    "depends": ["base",'project','sale','account','web','portal','hr','crm','web_editor','hr_timesheet', 'sale_timesheet','timesheet_grid'],
    "data": [
        "views/website_portal_templates.xml",
        "views/project_view.xml",
        "views/project_tasks_settings_view.xml",
        "views/leave_type_view.xml",
        "views/employee_sheets_view.xml",
        "views/employee_customizations_view.xml",
        "views/task_customizations_view.xml",
        "views/contract_customizations_view.xml",
        "views/custom_csv_export.xml",
        'views/account_move_view.xml',
        'views/account_tax_view.xml',
        "views/contact_customizations_view.xml",
        "views/holiday_view.xml",
        "views/sale_order_customizations_view.xml",
        "views/report_templates.xml",
        "views/res_partner_view.xml",
        "views/res_config.xml",
        "report/report_sheet_timesheets.xml",
        'report/report_sheet.xml',
        "report/report_invoice_custom.xml",
        "data/emails.xml",
        "data/cron.xml",
        "security/ir.model.access.csv",
        'wizard/hr_holidays_new_leaves_views.xml',
        'wizard/hr_holidays_new_leaves_views_employee.xml',
        'views/hr_timesheet_views.xml',
        'views/company_customizations.xml',
        'views/product_view.xml'
    ],
    "application": True,
    "installable": True,
    'assets': {
        'web.assets_frontend': [
            "/dws_dae_custom/static/src/js/website_portal.js",
            "/dws_dae_custom/static/src/js/portal_signature.js"
        ]
    }
}
