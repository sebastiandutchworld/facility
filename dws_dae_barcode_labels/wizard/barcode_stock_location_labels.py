# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class BarcodeStockLocationLabelsWiz(models.TransientModel):
    _name = "barcode.stock.location.labels.wiz"
    _description = 'Barcode Product Template Labels Wizard'

    product_barcode_ids = fields.One2many('barcode.stock.location.labels.wiz.line', 'label_id', 'Product Barcode')

    @api.model
    def default_get(self, fields):
        res = super(BarcodeStockLocationLabelsWiz, self).default_get(fields)
        active_ids = self._context.get('active_ids')
        location_ids = self.env['stock.location'].browse(active_ids)
        barcode_lines = []
        for location in location_ids:
            barcode_lines.append((0,0, {
                'label_id' : self.id,
                'location_id' : location.id,
                'qty' : 1,
            }))
        res.update({
            'product_barcode_ids': barcode_lines
        })
        return res

    def print_barcode_labels(self):
        self.ensure_one()
        [data] = self.read()
        barcode_config = \
                    self.env.ref('dws_dae_barcode_labels.barcode_labels_config_data')
        if not barcode_config.barcode_currency_id or not barcode_config.barcode_currency_position:
            raise UserError(_('Barcode Configuration fields are not set in data (Inventory -> Settings -> Barcode Configuration)'))
        data['barcode_labels'] = data['product_barcode_ids']
        barcode_lines = self.env['barcode.stock.location.labels.wiz.line'].browse(data['barcode_labels'])
        # barcode_lines = self.env['barcode.product.template.labels.wiz.line'].browse(data['barcode_labels'])
        datas = {
             'ids': [1],
             'model': 'barcode.stock.location.labels.wiz',
             'form': data
        }
        return self.env.ref('dws_dae_barcode_labels.printed_stock_location_barcode_labels_id').report_action(barcode_lines, data=datas)


class BarcodeStockLocationLabelsLine(models.TransientModel):
    _name = "barcode.stock.location.labels.wiz.line"
    _description = 'Barcode Product Labels Line'
    
    label_id = fields.Many2one('barcode.stock.location.labels.wiz', 'Barcode labels')
    location_id = fields.Many2one('stock.location', 'Location')
    qty = fields.Integer('Barcode', default=1)