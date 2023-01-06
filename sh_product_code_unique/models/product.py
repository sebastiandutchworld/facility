# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, api, _
from odoo.exceptions import ValidationError


class Product(models.Model):
    _inherit = 'product.product'

    @api.constrains('default_code')
    def _check_default_code(self):
        product_id = self.env['product.product'].sudo().search(
            [('default_code','!=',False),('default_code', '=', self.default_code), ('id', '!=', self.id)])
        if product_id:
            raise ValidationError(_('Internal reference must be unique!'))
