from odoo import api, fields, models

class ResPartnerCustom(models.Model):
    _inherit = 'res.partner'

    exact_customer_account_receivable = fields.Char()
    ubl_invoice = fields.Boolean('Ubl invoice')
    pdf_merge = fields.Boolean('Merge invoice PDF with timesheet PDF')
    company_registry = fields.Char()
    company_oin = fields.Char('OIN')
    
