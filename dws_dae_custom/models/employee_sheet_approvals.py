# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools
from datetime import datetime,timedelta
import uuid

class EmployeeSheetApprovals(models.Model):
    _name = 'employee_sheet.approvals'

    def _get_default_access_token(self):
        return str(uuid.uuid4())

    partner_id = fields.Many2one('res.partner', string='Customer')
    sheet_id = fields.Many2one('employee.sheet', string='Employee timesheet')
    project_id = fields.Many2one('project.project', string='Project')
    action_at = fields.Datetime("Last action time")
    status = fields.Selection([('0', 'New'),('1', 'Approved'), ('2', 'Rejected')])
    access_token = fields.Char('Security Token', copy=False,default=_get_default_access_token)
    pdf_report = fields.Binary('Pdf report', readonly=True, attachment=False)
    notes = fields.Char("Notes")

    @api.model
    def schedule_approval_reminder(self):
        # nrdays = 3
        # email_context = self.env.context.copy()
        # approval_ids = self.search(["|",("status","=",0),("status","=",False),('write_date', '<', fields.Datetime.to_string(datetime.today() - timedelta(days=nrdays)))])
        #
        # if (approval_ids):
        #     for approval in approval_ids:
        #         email_context.update({
        #             'email_to': approval.partner_id.email,
        #             'token': approval.access_token,
        #             'name': approval.partner_id.name,
        #             'employee_name': approval.sheet_id.user_id.partner_id.name,
        #             'sheet_id': approval.sheet_id
        #         })
        #
        #         template = self.env.ref('dws_dae_custom.email_template_data_approval_reminder')
        #         self.env['mail.template'].sudo().browse(template.id).with_context(email_context).send_mail(approval.sheet_id.id)
        self.mail_approval_reminders(self.generate_approval_reminder_ids())

    def generate_approval_reminder_ids(self):
        nrdays = 3
        approval_ids = self.search(["|", ("status", "=", 0), ("status", "=", False), (
        'write_date', '<', fields.Datetime.to_string(datetime.today() - timedelta(days=nrdays)))])
        print('approval_ids=', approval_ids)

        reminder_ids = []
        if (approval_ids):
            for approval in approval_ids:
                reminder_ids.append(approval.id)
                print('approval sheet id=', approval.sheet_id.id)
        return reminder_ids

    def mail_approval_reminders(self, approval_ids):
        email_context = self.env.context.copy()
        approvals = self.search([('id', 'in', approval_ids)])
        for approval in approvals:
            email_context.update({
                'email_to': approval.partner_id.email,
                'token': approval.access_token,
                'name': approval.partner_id.name,
                'employee_name': approval.sheet_id.user_id.partner_id.name,
                'sheet_id': approval.sheet_id
            })

            template = self.env.ref('dws_dae_custom.email_template_data_approval_reminder')
            self.env['mail.template'].sudo().browse(template.id).with_context(email_context).send_mail(approval.sheet_id.id)

    def button_action_approval_reminder(self):
        active_ids = self.env.context.get('active_ids', []) or []
        print('active ids for approvals=', active_ids)
        approver_ids = self.search([('id', 'in', self.generate_approval_reminder_ids())])
        mail_to_ids = []
        for approver in approver_ids:
            if approver.sheet_id.id in active_ids:
                mail_to_ids.append(approver.id)
        self.mail_approval_reminders(mail_to_ids)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    reminder_approver_allow = fields.Boolean("Approval Reminder",
        help="If checked, send an email to all users who not approved their timesheet")
    reminder_approver_delay = fields.Integer("Number of days")