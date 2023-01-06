# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Candidroot Solutions Pvt. Ltd.

from odoo import fields, api, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    peppol_boolean = fields.Boolean("PEPPOL validation")
    peppol_email = fields.Many2one('res.partner', string="Partner")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        res['peppol_boolean'] = self.env['ir.config_parameter'].sudo().get_param('peppol_boolean')
        res['peppol_email'] = int(self.env['ir.config_parameter'].sudo().get_param('peppol_email'))

        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('peppol_boolean', self.peppol_boolean)
        self.env['ir.config_parameter'].sudo().set_param('peppol_email', self.peppol_email.id)

        super(ResConfigSettings, self).set_values()

