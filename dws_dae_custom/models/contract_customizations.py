# -*- coding: utf-8 -*-

import datetime
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models, fields, api, exceptions,_
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DFORMAT

class ContractCustomizations(models.Model):
    # _name = "contract.customizations"
    _inherit="hr.contract"

    notice_period = fields.Integer('Notice Period')
    tax_credit = fields.Boolean('\t\t\tTax Credit')
    # thirty_p_ruling = fields.Selection([('na','NA'), ('requested', 'Requested'), ('granted', 'Granted'), ('rejected', 'Rejected')], string='30% Ruling')
    # secondment_declaration = fields.Selection([('na', 'NA'), ('requested', 'Requested'), ('granted', 'Granted'), ('rejected', 'Rejected')], string='Secondment Declaration')
    lease_car = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Lease Car')
    type_kilometer_arrangement = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Kilometer Compensation')
    above_legal_leave = fields.Integer('Bovenwettelijk verlof voltijd (uren)')
    adv_leave = fields.Integer('ADV voltijd (uren)')
    # security_clearance = fields.Selection([('na','NA'), ('requested', 'Requested'), ('granted', 'Granted'), ('rejected', 'Rejected')], string='Security Clearance')
    # resource_calendar_id_changed = fields.Date()
    # resource_calendar_id_reference_name = fields.Char(compute="_resource_calendar_id_changed")

    state = fields.Selection([
        ('draft', 'New'),
        ('open', 'Running'),
        ('pending', 'To Renew'),
        ('close', 'Expired')
    ], string='Status', group_expand='_expand_states',
       track_visibility='onchange', help='Status of the contract', default='draft')

    # confirmation = fields.Boolean(string="Do you agree to Zero all leave hours for the employee concerned?",required=True)

    # @api.onchange('resource_calendar_id')
    # @api.multi
    # def _resource_calendar_id_changed(self):
    #     for rec in self:
    #         # if the contract hours are not set for the first time change date changed to today
    #         print('rec_id: ', rec.id)
    #         if rec.env['hr.contract'].search([('id', '=', rec.id)], limit=1).name != rec.resource_calendar_id_reference_name and rec.resource_calendar_id_reference_name:
    #             rec.resource_calendar_id_changed = datetime.datetime.now()
    #         rec.resource_calendar_id_reference_name = rec.resource_calendar_id.name
    #     print('resource_calendar_id_changed: ', rec.resource_calendar_id_changed)

    # not more than one contract in state 'open'
    @api.constrains('state')
    def _verify_state(self):
        contracts_open = self.search([('state', '=', 'open'), ('employee_id', '=', self.employee_id.id)])
        # print('contracts_open', contracts_open)
        # print(len(contracts_open))
        # print('name', self.name)
        if len(contracts_open) > 1:
            raise exceptions.ValidationError(_("An employee can have no more than one contract in state 'Running'"))



