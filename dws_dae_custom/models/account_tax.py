from odoo import api, fields, models

class AccountTaxCustom(models.Model):
    _inherit = 'account.tax'

    exact_btw_code = fields.Char()