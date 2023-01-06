# -*- coding: utf-8 -*-
from odoo import api, models, fields

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    analytic_account = fields.Many2one('account.analytic.account', string='Analytic account')

    @api.onchange('analytic_account')
    def _on_change_analyticaccount(self):
        for ol in self.order_line:
            ol.account_analytic_id = self.analytic_account.id