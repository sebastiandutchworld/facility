# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools

class EmployeeHours(models.Model):
    _name = 'employee.hours'

    _rec_name = 'id'

    employee_sheet_id = fields.Many2one('employee.sheet', string='Employee sheet')
    task_id = fields.Many2one('project.task',string='Task',readonly=True)
    date = fields.Date("Date")
    fromtime = fields.Datetime("From")
    totime = fields.Datetime("To")
    regular = fields.Float("Regular")
    overtime = fields.Float("Overtime")
    vacation = fields.Float("Vacation")
    adv = fields.Float("Adv")
    illness = fields.Float("Illness")
    nw = fields.Float("NW")


    approved_by = fields.Many2many('res.partner', string='Approved by', help="List of customers who approved the timesheet.")
    status = fields.Selection([('1', 'Confirmed by employee'), ('2', 'Approved by BO'), ('3', 'Approved by customers'), ('4', 'Done')])
    notes = fields.Char("Notes")



