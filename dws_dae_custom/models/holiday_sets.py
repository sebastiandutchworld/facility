# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools

class ProjectHolidaysets(models.Model):
    _name = 'project.holidaysets'


    project_id = fields.Many2one('project.project', string='Project')
    date = fields.Date("Date")
    type = fields.Selection([('0', 'Holiday'),('1', 'Work day')])
    notes = fields.Char("Notes")

