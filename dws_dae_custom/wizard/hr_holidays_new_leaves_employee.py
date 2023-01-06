# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time
import re

from odoo import api, fields, models, _
from datetime import timedelta, date, datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning

class HolidaysSummaryDept(models.TransientModel):
    _name = 'hr.holidays.leave.employee'

    employee = fields.Many2one('hr.employee')
    clicked = fields.Boolean(default=False)

    def create_annual_leaves(self):
        contract = self.env['hr.contract'].sudo().search(
            [('employee_id', '=', self.employee.id), ('state', '=', 'open')], limit=1)  # contract with no end date
        if contract:
            if not self.clicked and int(self.employee.collaborator_id[0]) != 5 and contract.resource_calendar_id.name != 'oproepkracht':
                self.clicked = True
                legal_leave_days = float(self.env['ir.config_parameter'].sudo().get_param('legal_leave'))
                contract_hours = 0

                if not contract:
                    # "Er is geen contract in met de status 'In dienst' gevonden"
                    raise ValidationError(_("There is no contract with state 'Running'"))
                number_of_all_days = 0.0
                number_of_adv_days = 0.0
                if contract:
                    contract_hours = contract.resource_calendar_id.contract_hours
                    number_of_all_days = (contract.above_legal_leave / 8)
                    number_of_adv_days = (contract.adv_leave / 8)
                leave_types = []
                company_id = self.employee.company_id.id
                number_of_days = 0.0
                # 1 = Daedalus, 3 = EML
                if company_id == 1:
                    leave_types.append(1)
                    leave_types.append(12)
                    leave_types.append(3)
                elif company_id == 3:
                    leave_types.append(5)
                    leave_types.append(13)
                    leave_types.append(11)
                for leave_type in self.env['hr.leave.type'].browse(leave_types):
                    start_date = contract.date_start
                    start = fields.Date.from_string(start_date)
                    name = leave_type.name + ' ' + str(start.year)
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
                    allocation_date = date(start.year, 1, 1)
                    leave = self.env['hr.leave.allocation'].create({
                        'name': _('%s') % name, # leave type + year
                        'holiday_status_id': leave_type.id, # depending of selection and employee company
                        'number_of_days': self.round_to_half(number_of_days * self._calculate_year_ratio(start)), # from working scedule in contract hours
                        'holiday_type': 'employee',
                        'employee_id': self.employee.id,
                        'allocation_date': start_date, # 01-01-[selection]
                        'expiration_date': fields.Date.to_string(allocation_date + relativedelta(months=int(leave_type.availability)) - relativedelta(days=1)),
                    })
                    leave.action_confirm()
                    leave.action_validate()

    def _calculate_year_ratio(self, input_date):
        print(input_date.year)
        days_in_year = date(input_date.year, 12, 31).timetuple().tm_yday
        day_of_year = input_date.timetuple().tm_yday
        print('days in year', days_in_year)
        print('day of year', day_of_year)
        ratio = (days_in_year - day_of_year) / days_in_year
        print("ratio", ratio)
        return ratio

    def round_to_half(self, number):
        return round(number * 2) / 2
