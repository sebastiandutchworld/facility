# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time
import re

from odoo import api, fields, models, _
from datetime import timedelta, date, datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning

class HolidaysSummaryDept(models.TransientModel):
    _name = 'hr.holidays.leave'

    allocation_year = fields.Char()
    ll = fields.Boolean('Wettelijk verlof')
    all = fields.Boolean('Bovenwettelijk verlof')
    adv = fields.Boolean('ADV')
    clicked = fields.Boolean(default=False)

    @api.constrains('allocation_year')
    def _raise_allocation_year_error(self):
        for rec in self:
            if not rec._valid_year_format(rec.allocation_year):
                raise ValidationError('Jaar is niet volgens het formaat "20??". Voer een geldig jaar in.')

    def _valid_year_format(self, input):
        match = re.match('20[0-9]{2}$', input)
        if match:
            return True
        else:
            return False

    def create_annual_leaves(self):
        # for each portal user create leaves for year [selection] of type [selection]
        if not self.clicked:
            self.clicked = True
            employees = self.env['hr.employee'].search([('user_id.share', '=', True)])
            legal_leave_days = float(self.env['ir.config_parameter'].sudo().get_param('legal_leave'))
            for employee in employees:
                if employee.collaborator_id:
                    contract = self.env['hr.contract'].sudo().search(
                        [('employee_id', '=', employee.id), ('state', '=', 'open')],
                        limit=1)  # contract with no end date
                    if contract:
                        # if not employee id starts with 5
                        if int(employee.collaborator_id[0]) != 5 and contract.resource_calendar_id.name != 'oproepkracht':
                            contract_hours = 0

                            number_of_all_days = 0.0
                            number_of_adv_days = 0.0
                            contract_hours = contract.resource_calendar_id.contract_hours
                            number_of_all_days = (contract.above_legal_leave / 8)
                            number_of_adv_days = (contract.adv_leave / 8)
                            leave_types = []
                            company_id = employee.company_id.id
                            number_of_days = 0.0
                            # 1 = Daedalus, 3 = EML
                            if self.ll:
                                if company_id == 1:
                                    leave_types.append(1)
                                elif company_id == 3:
                                    leave_types.append(5)
                            if self.all:
                                if company_id == 1:
                                    leave_types.append(12)
                                elif company_id == 3:
                                    leave_types.append(13)
                            if self.adv:
                                if company_id == 1:
                                    leave_types.append(3)
                                elif company_id == 3:
                                    leave_types.append(11)
                            for leave_type in self.env['hr.leave.type'].browse(leave_types):
                                name = leave_type.name + ' ' + self.allocation_year
                                create_leave = len(self.env['hr.leave.allocation'].search([('employee_id', '=', employee.id), ('name', '=', name)])) == 0
                                if create_leave:
                                    if int(leave_type.type) == 1:
                                        number_of_days = ((contract_hours / 40) * legal_leave_days)
                                    elif int(leave_type.type) == 2:
                                        number_of_days = ((contract_hours / 40) * number_of_adv_days)
                                        if number_of_days == 0:
                                            continue
                                    elif int(leave_type.type) == 3:
                                        number_of_days = ((contract_hours / 40) * number_of_all_days)
                                        if number_of_days == 0:
                                            continue
                                    allocation_date = date(int(self.allocation_year), 1, 1)
                                    leave = self.env['hr.leave.allocation'].create({
                                        'name': _('%s') % name, # leave type + year
                                        'holiday_status_id': leave_type.id, # depending of selection and employee company
                                        'number_of_days': number_of_days, # from working scedule in contract hours
                                        'holiday_type': 'employee',
                                        'employee_id': employee.id,
                                        'allocation_date': fields.Date.to_string(allocation_date), # 01-01-[selection]
                                        'expiration_date': fields.Date.to_string(allocation_date + relativedelta(months=int(leave_type.availability)) - relativedelta(days=1)),
                                    })
                                    leave.action_confirm()
                                    leave.action_validate()
            # self.clicked = False
