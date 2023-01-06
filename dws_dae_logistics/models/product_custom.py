# -*- coding: utf-8 -*-
from odoo import api, models, fields

class ProductCustom(models.Model):
    _inherit = 'product.template'

    nsn = fields.Char(string='NSN')
    product_conditions = fields.Many2one(string="Product Conditions", comodel_name='product.condition')


    @api.onchange('nsn')
    def onchange_nsn(self):
        """ """
        temp = ''
        if self.nsn:
            for i in range(0,len(self.nsn)):
                if self.nsn[i] != '-':
                    temp = temp + self.nsn[i]
            self.nsn = temp

            if len(self.nsn) != 13:
                warning = { 'title': 'Warning!', 'message' : 'NSN number incorrect length, should be 13 character long.'}
                return {'warning': warning}

        if self.nsn:
            self.nsn = self.nsn[0:4] + "-" + self.nsn[4:6] + "-" + self.nsn[6:9] + "-" + self.nsn[9:13]   

