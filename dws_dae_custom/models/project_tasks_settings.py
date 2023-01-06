# -*- coding: utf-8 -*-

from odoo import api, models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    project_other_hours = fields.Many2one('project.project', "Project 'Other Hours'",related='company_id.project_other_hours', store=True, readonly=False)
    #project_other_hours = fields.Many2one('project.project', "Project 'Other Hours'")
    task_vacation = fields.Many2one('project.task', "Task 'Vacation'",related='company_id.task_vacation', store=True, readonly=False)
    task_adv = fields.Many2one('project.task', "Task 'Adv'",related='company_id.task_adv', store=True, readonly=False)
    task_all = fields.Many2one('project.task', "Task 'Above legal'",related='company_id.task_all', store=True, readonly=False)
    task_illness = fields.Many2one('project.task', "Task 'Illness'",related='company_id.task_illness', store=True, readonly=False)
    task_nw = fields.Many2one('project.task', "Task 'Non Working'", related='company_id.task_nw', store=True, readonly=False)
    task_update = fields.Boolean(default=False)
    employee_timesheet_reminder_interval = fields.Integer('Reminder Interval')
    legal_leave = fields.Float('Wettelijk verlof')
    hr_approver_partner = fields.Many2one('res.partner','HR Approver')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        values = {}
        values['employee_timesheet_reminder_interval'] = int(self.env['ir.config_parameter'].sudo().get_param('employee_timesheet_reminder_interval'))
        values['legal_leave'] = float(self.env['ir.config_parameter'].sudo().get_param('legal_leave'))
        values['hr_approver_partner'] = int(self.env['ir.config_parameter'].sudo().get_param('hr_approver_partner'))
        res.update(values)
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('employee_timesheet_reminder_interval', self.employee_timesheet_reminder_interval)
        self.env['ir.config_parameter'].sudo().set_param('legal_leave', self.legal_leave)
        self.env['ir.config_parameter'].sudo().set_param('hr_approver_partner', self.hr_approver_partner.id)

    # @api.onchange('project_other_hours')
    # def _clear_tasks(self):
    #     if self.project_other_hours.id != int(self.env['ir.config_parameter'].sudo().get_param('project_other_hours')) or self.task_update:
    #         self.task_update = True
    #         self.task_vacation = False
    #         self.task_adv = False
    #         self.task_illness = False

    @api.onchange('project_other_hours')
    def _clear_tasks(self):
        if not self.task_update:
            self.task_update = True
        else:
            self.task_vacation = False
            self.task_adv = False
            self.task_illness = False
            self.task_nw = False