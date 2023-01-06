# -*- coding: utf-8 -*-
from odoo import api, models, fields

class ProductTemplate(models.Model):
    _inherit = "product.template"

    vendor_product_name = fields.Char(string="Vendor Product Name", index=True)#, compute="_compute_vendor_name")
    vendor_product_code = fields.Char(string="Vendor Product Code", index=True)#, compute="_compute_vendor_name")

