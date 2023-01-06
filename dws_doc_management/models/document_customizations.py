# -*- coding: utf-8 -*-

import datetime, re
from odoo import models, fields, api, exceptions,_

class DocumentCustomizations(models.Model):
    _inherit="documents.document"

    valid_from = fields.Date('Valid From')
    valid_until = fields.Date('Valid Until')
    signal_period_months = fields.Integer('Signal Period (Months)')
    activity_created = fields.Boolean()

    # @api.onchange('name')
    # def document_actions2(self):
    #     print('name changed')
    #     pattern = '^(\d{3,6}).*'
    #     result = re.match(pattern, self.name)
    #     if result and result.group(1):
    #         print('it is an employee document')
    #         # set employee document tag
    #         tag_id = self.env['documents.tag'].search([('name', '=', 'Employees Documents')], limit=1)
    #         self.tag_ids = [(4, tag_id[0].id)] if tag_id else [(0, 0, {'name': 'Employees Documents'})]
    #         # add a tag when valid_until is set
    #         if self.valid_until:
    #             tag_id = self.env['documents.tag'].search([('name', '=', 'To Validate')], limit=1)
    #             self.tag_ids = [(4, tag_id[0].id)] if tag_id else [(0, 0, {'name': 'To Validate'})]
    #         # set owner of document
    #         collaborator_id = result.group(1)
    #         employee = self.env['hr.employee'].search([('collaborator_id', 'ilike', collaborator_id)], limit=1)
    #         if employee:
    #             self.owner_id = employee.user_id.id

    # @api.onchange('valid_until')
    # def create_activity(self):
    #     if not self.activity_created:
    #         date_deadline = self.valid_until - datetime.timedelta((30 * self.signal_period_months))
    #         print(date_deadline)
    #         activity_type_id = self.env['activity.type'].search(['name', '=', 'Todo'], limit=1)
    #         self.env['mail.activity'].create({
    #             'res_id': self.env.user_id.partner_id.id,
    #             'res_model_id': self.env['ir.model']._get(self._name).id,
    #             'activity_type_id': activity_type_id.id,
    #             'summary': "Document needs to be renewed",
    #             'user_id': 112,
    #             'date_deadline': date_deadline
    #         })
    #         self.activity_created = True




