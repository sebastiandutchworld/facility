# -*- coding: utf-8 -*-
from odoo import api, models, fields


class ProductCondition(models.Model):
    # _name = "product.state"
    _name = "product.condition"
    _description = "Product Condition"
    
    name = fields.Char(string='Name', required=True)    
    code = fields.Char(string='Code', required=True)
    
    product_custom = fields.One2many('product.template', 'product_conditions', string="Product Condition")
    

    def name_get(self):
        result = []
        for record in self:
            name = "[" + record.code + "]" + record.name
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        if args is None:
            args = []
        domain = args + ['|',('name', operator, str(name)), ('code', operator, str(name))]

        return self._search(domain, limit=limit,access_rights_uid=name_get_uid)
        
        

            


