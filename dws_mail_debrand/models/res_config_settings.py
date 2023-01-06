# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CustomSalesMail(models.TransientModel):
    _inherit = "res.config.settings"

    disable_buttons = fields.Boolean(string="Disable buttons in emails for online viewing of entities")

    @api.model
    def get_values(self):
        res = super(CustomSalesMail, self).get_values()
        res.update(
            disable_buttons=self.env['ir.config_parameter'].sudo().get_param(
                'dws_mail_debrand.disable_buttons'),
        )
        return res

    def set_values(self):
        super(CustomSalesMail, self).set_values()
        param = self.env['ir.config_parameter'].sudo()

        field1 = self.disable_buttons or False

        param.set_param('dws_mail_debrand.disable_buttons', field1)
