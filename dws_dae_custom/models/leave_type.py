# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools

class LeaveType(models.Model):
    _inherit = 'hr.leave.type'

    type = fields.Selection([('1', 'Wettelijk verlof'), ('2', 'ADV'),('3', 'Bovenwettelijk verlof')])
    availability = fields.Integer('Beschikbaarheid (maanden)')

