# Copyright 2015 ABF OSIELL <https://osiell.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# noinspection PyStatementEffect
{
    "name": "customizations for Gearboks logistics",
    "version": "13.0.1.0.1",
    "author": "Dutchworld Solutions",
    "license": "AGPL-3",
    "website": "https://dutchworld.nl",
    "category": "Tools",
    'description': """
    addition of the NSN field and product state field.
     Ticket #3802, #3803
    """,
    "depends": ["base",'product','stock', 'sale'],
    "data": [
        "views/product_condition_view.xml",
        "views/product_custom_views.xml",
        "views/po_customizations.xml",
        "security/ir.model.access.csv",
        "report/sale_report_template_custom.xml",
        "report/deliveryslip_report_custom.xml",
        "report/report_deliveryslip_coc.xml",
        "report/slips_report.xml",
        "report/report_purchaseorder.xml",	
    ],
    "application": True,
    "installable": True,
}
