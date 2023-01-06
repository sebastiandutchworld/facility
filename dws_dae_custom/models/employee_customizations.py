# -*- coding: utf-8 -*-

import datetime,time
import re
import logging
from odoo.exceptions import UserError
from odoo import api, models, fields
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DFORMAT
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)

class EmployeeCustomizations(models.Model):
    _inherit = "hr.employee"

    collaborator_id = fields.Char('Collaborator ID')
    bsn_number = fields.Char('BSN Number')
    phone = fields.Char('Phone', related='address_home_id.phone')
    mobile = fields.Char('Mobile', related='address_home_id.mobile')
    #address_home_id = fields.Many2one(
    #    'res.partner', 'Private Address', help='Enter here the private address of the employee, not the one linked to your company.',
    #    groups="hr.group_hr_user", compute='_compute_address_home_id', store=True)
    address_home_id = fields.Many2one(
            'res.partner', related="user_id.partner_id",readonly=True)
    foreign_address = fields.Many2one('res.partner', 'Foreign Address', compute='_compute_fields')
    emergency_contact_address = fields.Many2one('res.partner', 'Emergency Contact', compute='_compute_fields')
    #lease_car_license_plate = fields.Char('Lease Car License Plate')
    tasks_count = fields.Char(compute='_tasks_count', string='Tasks')
    thirty_p_ruling = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='30% Ruling', default='no')
    lease_car = fields.Char(compute='_lease_car')
    banking_hours_start_date = fields.Date('Banking Start Date')
    banking_hours_amount = fields.Float('Banking Start Hours')
    banking_hours = fields.Float(compute='_banking_hours')
    contract_hours = fields.Float(compute='_contract_hours')
    #vacation_hours_assigned = fields.Float('Vacation hours assigned', compute='_adv_vacation_hours')
    # vacation_hours_remaining = fields.Float('Vacation hours left',compute='_adv_vacation_hours')
    # adv_hours_assigned = fields.Float('Adv hours assigned', compute='_adv_vacation_hours')
    # adv_hours_remaining = fields.Float('Adv hours left',compute='_adv_vacation_hours')
    transport_last_year = fields.Float('Transport vorig jaar',compute='_adv_vacation_hours')
    allocated_this_year = fields.Float('Toegewezen dit jaar', compute='_adv_vacation_hours')
    balance_this_year = fields.Float('Huidig saldo', compute='_adv_vacation_hours')
    buildup_this_year = fields.Float('Opgebouwd', compute='_adv_vacation_hours')
    booked_this_year = fields.Float('Geboekte uren', compute='_adv_vacation_hours')
    buildup_this_year_all = fields.Float('Opgebouwd', compute='_adv_vacation_hours')
    booked_this_year_all = fields.Float('Geboekte uren', compute='_adv_vacation_hours')
    transport_last_year_all = fields.Float('Transport vorig jaar', compute='_adv_vacation_hours')
    allocated_this_year_all = fields.Float('Toegewezen dit jaar', compute='_adv_vacation_hours')
    balance_this_year_all = fields.Float('Huidig saldo', compute='_adv_vacation_hours')
    transport_last_year_adv = fields.Float('Transport vorig jaar', compute='_adv_vacation_hours')
    allocated_this_year_adv = fields.Float('Toegewezen dit jaar', compute='_adv_vacation_hours')
    buildup_this_year_adv = fields.Float('Opgebouwd', compute='_adv_vacation_hours')
    booked_this_year_adv = fields.Float('Geboekte uren', compute='_adv_vacation_hours')
    balance_this_year_adv = fields.Float('Huidig saldo', compute='_adv_vacation_hours')
    employee_label = fields.Char('Label', compute='_compute_label')
    reference_date = fields.Date('Referentiedatum')
    order_ids = fields.Many2many('sale.order', compute='_compute_order_ids', string='Contracten')
    order_count = fields.Integer(compute='_compute_order_ids', string='Verkoopcontracten')
    sheet_count = fields.Integer(compute='_compute_sheet_count', string='Portal Urenstaten')
    coach_id = fields.Many2one('hr.employee', domain=[])

    def _compute_sheet_count(self):
        sheets_data = self.env['employee.sheet'].sudo().read_group([('user_id', '!=', False)], ['user_id'], ['user_id'])
        result = dict((data['user_id'][0], data['user_id_count']) for data in sheets_data)
        for rec in self:
            rec.sheet_count = result.get(rec.user_id.id, 0)

    def _compute_order_ids(self):
        for rec in self:
            rec.order_count = 0
            user_id = rec.user_id.id

            if user_id:
                tasks_ids = self.env['project.task'].search([('user_ids', '=', user_id)])
                order_ids = tasks_ids.mapped('sale_line_id.order_id')
                rec.order_ids = order_ids
                rec.order_count = len(order_ids)
                

    def action_view_order(self):
        self.ensure_one()
        action = self.env.ref('sale.action_orders')
        list_view_id = self.env.ref('sale.view_order_tree').id
        form_view_id = self.env.ref('sale.view_order_form').id

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [False, 'kanban'], [form_view_id, 'form'], [False, 'graph'], [False, 'calendar'], [False, 'pivot'], [False, 'graph']],
            'target': action.target,
            'res_model': action.res_model,
            'domain': "[('id','in',%s)]" % self.order_ids.ids,
        }
        return result

    @api.depends("user_id.partner_id") # net veranderd
    def _compute_address_home_id(self):
        for rec in self:
            rec.address_home_id = rec.user_id.partner_id

    def _contract_hours(self):
        for rec in self:
            contract_hours = 0
            resource_calendar = self.env['hr.contract'].sudo().search(
                [('employee_id', '=', rec.id)])
            if resource_calendar:
                resource_calendar_id = resource_calendar[0].resource_calendar_id
                attendances = self.env['resource.calendar.attendance'].sudo().search(
                [('calendar_id', '=', resource_calendar_id.id)])
                if attendances:
                    for attendance in attendances:
                        contract_hours += attendance.hour_to - attendance.hour_from

            rec.contract_hours = contract_hours

    def calc_vac_hours(self,reference_date):
        #'all' stands for Above Legal Leave

        task_mappings = {}
        task_mappings['task_vacation'] = self.user_id.company_id.task_vacation.id
        task_mappings['task_adv'] = self.user_id.company_id.task_adv.id
        task_mappings['task_all'] = self.user_id.company_id.task_all.id

        legal_holiday_status = self.env['hr.leave.type'].search([("company_id", "=", self.user_id.company_id.id), ("type", "=", 1)], limit=1)
        adv_holiday_status = self.env['hr.leave.type'].search([("company_id", "=", self.user_id.company_id.id), ("type", "=", 2)], limit=1)
        all_holiday_status = self.env['hr.leave.type'].search([("company_id", "=", self.user_id.company_id.id), ("type", "=", 3)], limit=1)
        day_of_year = datetime.datetime.strptime(str(reference_date),"%Y-%m-%d").timetuple().tm_yday
        remaining_days_of_year = 365 - day_of_year

        _logger.info('legal holiday: %s', legal_holiday_status)

        buildup_legal_holiday_hours = 0
        buildup_adv_holiday_hours = 0
        buildup_all_holiday_hours = 0

        buildup_days = 0
        nr_legal_hours = 0
        nr_legal_hours_ly = 0
        nr_legal_hours_cy = 0
        vacation_hours_cy = 0
        vacation_hours_cy_for_warning = 0
        vacation_hours_cy_for_transp = 0
        vacation_hours_ly = 0
        vacation_hours_cy_rec_first = 0

        nr_adv_hours = 0
        nr_adv_hours_ly = 0
        nr_all_hours_ly = 0
        nr_all_hours_cy = 0
        nr_adv_hours_cy = 0
        adv_hours_ly = 0
        all_hours_ly = 0
        all_hours_cy = 0
        adv_hours_cy = 0

        balance_cy = 0
        balance_cy_adv = 0
        balance_cy_all = 0
        balance_ly = 0
        balance_ly_adv = 0
        balance_ly_all = 0
        balance_ly_transp = 0
        vacation_hours_cy_for_transp = 0
        transp_diff = 0

        if legal_holiday_status:
            allowed_holidays = self.env['hr.leave.allocation'].search(
            [("employee_id", "=", self.id),("expiration_date",">=",reference_date),("allocation_date","<=",reference_date)])
            _logger.info('employee_id: %s', self.id)
            _logger.info('refdate: %s', reference_date)
            _logger.info('allowed_holidays: %s', allowed_holidays)
            for allowed_holiday in allowed_holidays:
                if datetime.datetime.strptime(str(allowed_holiday.allocation_date),"%Y-%m-%d").year < datetime.datetime.strptime(str(reference_date),"%Y-%m-%d").year:
                    _logger.info('last year!!: %s', allowed_holiday.id)
                    if allowed_holiday.holiday_status_id.id == legal_holiday_status[0].id:
                        #nr_legal_hours += allowed_holiday.number_of_days * 8
                        nr_legal_hours_ly = allowed_holiday.number_of_days * 8
                        vacation_hours_ly_rec = self.env['account.analytic.line'].search(
                            [("employee_id", "=", self.id), ("task_id", "=", task_mappings['task_vacation']),
                             ("date", ">=", allowed_holiday.allocation_date),
                             ("date", "<=", datetime.datetime.strptime(str(allowed_holiday.allocation_date),"%Y-%m-%d").strftime('%Y-12-31'))])
                        if vacation_hours_ly_rec:
                            for vac_hour_rec in vacation_hours_ly_rec:
                                vacation_hours_ly += vac_hour_rec.unit_amount
                        balance_ly = nr_legal_hours_ly - vacation_hours_ly
                        _logger.info('nr_legal_hours_ly: %s', nr_legal_hours_ly)
                        _logger.info('vacation_hours_ly: %s', vacation_hours_ly)
                    if allowed_holiday.holiday_status_id.id == adv_holiday_status[0].id:
                        nr_adv_hours_ly += allowed_holiday.number_of_days * 8
                        adv_hours_ly_rec = self.env['account.analytic.line'].search(
                            [("employee_id", "=", self.id), ("task_id", "=", task_mappings['task_adv']),
                             ("date", ">=", allowed_holiday.allocation_date),
                             ("date", "<=", datetime.datetime.strptime(str(allowed_holiday.allocation_date), "%Y-%m-%d").strftime('%Y-12-31'))])
                        if adv_hours_ly_rec:
                            for adv_hour_rec in adv_hours_ly_rec:
                                adv_hours_ly += adv_hour_rec.unit_amount
                    if allowed_holiday.holiday_status_id.id == all_holiday_status[0].id:
                        nr_all_hours_ly += allowed_holiday.number_of_days * 8
                        # _logger.info('test here: %s', nr_all_hours_ly)
                        all_hours_ly_rec = self.env['account.analytic.line'].search(
                            [("employee_id", "=", self.id), ("task_id", "=", task_mappings['task_all']),
                             ("date", ">=", allowed_holiday.allocation_date),
                             ("date", "<=",
                              datetime.datetime.strptime(str(allowed_holiday.allocation_date), "%Y-%m-%d").strftime(
                                  '%Y-12-31'))])
                        if all_hours_ly_rec:
                            for all_hour_rec in all_hours_ly_rec:
                                all_hours_ly += all_hour_rec.unit_amount

                else:
                    validity = datetime.datetime.strptime(str(datetime.datetime.strptime(str(reference_date), "%Y-%m-%d").strftime('%Y-12-31')),"%Y-%m-%d").timetuple().tm_yday - datetime.datetime.strptime(str(allowed_holiday.allocation_date),
                                                                "%Y-%m-%d").timetuple().tm_yday + 1
                    buildup_days = day_of_year - datetime.datetime.strptime(str(allowed_holiday.allocation_date),
                                                                            "%Y-%m-%d").timetuple().tm_yday + 1
                    if allowed_holiday.holiday_status_id.id == legal_holiday_status[0].id:
                        nr_legal_hours_cy = allowed_holiday.number_of_days * 8

                        vacation_hours_cy_rec_first = self.env['account.analytic.line'].search(
                            [("employee_id", "=", self.id), ("task_id", "=", task_mappings['task_vacation']),
                             (
                             "date", ">=", datetime.datetime.strptime(str(reference_date), "%Y-%m-%d").strftime('%Y-01-01')),
                             ("date", "<=", reference_date)])
                        if vacation_hours_cy_rec_first:
                            for vac_hour_rec in vacation_hours_cy_rec_first:
                                vacation_hours_cy_for_warning += vac_hour_rec.unit_amount

                        #let's check if we have a holiday allocation expiring this year and if we are past the expiration date
                        allowed_holiday_exp_cy = self.env['hr.leave.allocation'].search(
                            [("employee_id", "=", self.id), ("expiration_date", "<", reference_date),
                             ("expiration_date", ">", datetime.datetime.strptime(str(reference_date), "%Y-%m-%d").strftime('%Y-01-01'))])

                        if allowed_holiday_exp_cy:
                            vacation_hours_cy_rec_first = self.env['account.analytic.line'].search(
                                [("employee_id", "=", self.id), ("task_id", "=", task_mappings['task_vacation']),
                                 ("date", ">=", datetime.datetime.strptime(str(reference_date), "%Y-%m-%d").strftime('%Y-01-01')),
                                 ("date", "<=", allowed_holiday_exp_cy[0].expiration_date)])
                            #if we have some hours let's calculate how many hours we need to substract from the transported hours
                            if vacation_hours_cy_rec_first:
                                for vac_hour_rec in vacation_hours_cy_rec_first:
                                    vacation_hours_cy_for_transp += vac_hour_rec.unit_amount

                            #calculate last year transport
                            nr_legal_hours_ly = allowed_holiday_exp_cy.number_of_days * 8
                            vacation_hours_ly_rec = self.env['account.analytic.line'].search(
                                [("employee_id", "=", self.id), ("task_id", "=", task_mappings['task_vacation']),
                                 ("date", ">=", allowed_holiday_exp_cy.allocation_date),
                                 ("date", "<=",
                                  datetime.datetime.strptime(str(allowed_holiday_exp_cy.allocation_date), "%Y-%m-%d").strftime(
                                      '%Y-12-31'))])
                            vacation_hours_ly = 0
                            if vacation_hours_ly_rec:
                                for vac_hour_rec in vacation_hours_ly_rec:
                                    vacation_hours_ly += vac_hour_rec.unit_amount
                            balance_ly_transp = nr_legal_hours_ly - vacation_hours_ly
                            transp_diff = balance_ly_transp - vacation_hours_cy_for_transp

                        vacation_hours_cy_rec = self.env['account.analytic.line'].search(
                            [("employee_id", "=", self.id), ("task_id", "=", task_mappings['task_vacation']),
                             ("date", ">=", allowed_holiday.allocation_date),
                             ("date", "<=", reference_date)]) #maybe we need just < there?
                        if vacation_hours_cy_rec:
                            for vac_hour_rec in vacation_hours_cy_rec:
                                vacation_hours_cy += vac_hour_rec.unit_amount

                        buildup_legal_holiday_hours = buildup_days * nr_legal_hours_cy / validity
                        balance_cy = buildup_legal_holiday_hours - vacation_hours_cy

                    if allowed_holiday.holiday_status_id.id == adv_holiday_status[0].id:
                        nr_adv_hours_cy = allowed_holiday.number_of_days * 8
                        adv_hours_cy_rec = self.env['account.analytic.line'].search(
                            [("employee_id", "=", self.id), ("task_id", "=", task_mappings['task_adv']),
                             ("date", ">=", allowed_holiday.allocation_date),
                             ("date", "<=", reference_date)])
                        if adv_hours_cy_rec:
                            for adv_hour_rec in adv_hours_cy_rec:
                                adv_hours_cy += adv_hour_rec.unit_amount

                        buildup_adv_holiday_hours = buildup_days * nr_adv_hours_cy / validity
                        balance_cy_adv = buildup_adv_holiday_hours - adv_hours_cy

                    if allowed_holiday.holiday_status_id.id == all_holiday_status[0].id:
                        nr_all_hours_cy = allowed_holiday.number_of_days * 8
                        all_hours_cy_rec = self.env['account.analytic.line'].search(
                            [("employee_id", "=", self.id), ("task_id", "=", task_mappings['task_all']),
                             ("date", ">=", allowed_holiday.allocation_date),
                             ("date", "<=", reference_date)])
                        if all_hours_cy_rec:
                            for all_hour_rec in all_hours_cy_rec:
                                all_hours_cy += all_hour_rec.unit_amount

                        buildup_all_holiday_hours = buildup_days * nr_all_hours_cy / validity
                        balance_cy_all = buildup_all_holiday_hours - all_hours_cy





            balance_ly_adv = nr_adv_hours_ly - adv_hours_ly
            balance_ly_all = nr_all_hours_ly - all_hours_ly

        holiday_hours = {}

        if balance_ly > 0:
            holiday_hours['balance_cy'] = balance_cy + balance_ly + transp_diff
        else:
            if transp_diff < 0:
                holiday_hours['balance_cy'] = balance_cy + balance_ly_transp
            else:
                holiday_hours['balance_cy'] = balance_cy + vacation_hours_cy_for_transp

        holiday_hours['balance_ly'] = balance_ly
        holiday_hours['allocated_cy'] = nr_legal_hours_cy
        holiday_hours['taken_cy'] = vacation_hours_cy_for_warning
        holiday_hours['booked_cy'] = vacation_hours_cy
        holiday_hours['buildup_cy'] = buildup_legal_holiday_hours
        _logger.info('taken_cy: %s', vacation_hours_cy_for_warning)

        holiday_hours['balance_cy_adv'] = balance_cy_adv + balance_ly_adv
        holiday_hours['balance_ly_adv'] = balance_ly_adv
        holiday_hours['allocated_cy_adv'] = nr_adv_hours_cy
        holiday_hours['booked_cy_adv'] = adv_hours_cy
        holiday_hours['buildup_cy_adv'] = buildup_adv_holiday_hours

        holiday_hours['balance_cy_all'] = balance_cy_all + balance_ly_all
        holiday_hours['balance_ly_all'] = balance_ly_all
        holiday_hours['allocated_cy_all'] = nr_all_hours_cy
        holiday_hours['booked_cy_all'] = all_hours_cy
        holiday_hours['buildup_cy_all'] = buildup_all_holiday_hours
        return holiday_hours


    def _adv_vacation_hours(self):
        for rec in self:
            vac_hours = rec.calc_vac_hours(rec.reference_date or datetime.datetime.now().strftime('%Y-%m-%d'))
            rec.balance_this_year = vac_hours['balance_cy']
            rec.transport_last_year = vac_hours['balance_ly']
            rec.allocated_this_year = vac_hours['allocated_cy']
            rec.buildup_this_year = vac_hours['buildup_cy']
            rec.booked_this_year = vac_hours['booked_cy']

            rec.balance_this_year_adv = vac_hours['balance_cy_adv']
            rec.transport_last_year_adv = vac_hours['balance_ly_adv']
            rec.allocated_this_year_adv = vac_hours['allocated_cy_adv']
            rec.buildup_this_year_adv = vac_hours['buildup_cy_adv']
            rec.booked_this_year_adv = vac_hours['booked_cy_adv']

            rec.balance_this_year_all = vac_hours['balance_cy_all']
            rec.transport_last_year_all = vac_hours['balance_ly_all']
            rec.allocated_this_year_all = vac_hours['allocated_cy_all']
            rec.buildup_this_year_all = vac_hours['buildup_cy_all']
            rec.booked_this_year_all = vac_hours['booked_cy_all']

    def _lease_car(self):
        for rec in self:
            rec.lease_car = rec.contract_id.lease_car

    @api.onchange('address_home_id')
    def _compute_fields(self):
        for rec in self:
            hasforeign = False
            hasemergency = False
            for id in rec.address_home_id.child_ids:
                if id.type == 'foreign':
                    hasforeign = True
                    rec.foreign_address = id
                if id.type == 'emergency_contact':
                    hasemergency = True
                    rec.emergency_contact_address = id
            if hasforeign == False:
                rec.foreign_address = False
            if hasemergency == False:
                rec.emergency_contact_address = False

    def _tasks_count(self):
        tasks_data = self.env['project.task'].sudo().read_group([('user_ids', '!=', False)], ['user_ids'], ['user_ids'])
        result = dict((data['user_ids'][0], data['user_ids_count']) for data in tasks_data)
        for rec in self:
            rec.tasks_count = result.get(rec.user_id.id, 0)


    def _banking_hours(self):
        for rec in self:
            print(rec.contract_hours)

            # last date, first date
            hour_lines = rec.env['account.analytic.line'].sudo().search([('employee_id', '=', rec.id)])
            last_date = None
            for hour_line in hour_lines:
                hour_line_date = datetime.datetime.strptime(str(hour_line.date), DFORMAT)
                _logger.info('hour_line_date: %s', hour_line_date)
                if not last_date or hour_line_date > last_date:
                    last_date = hour_line_date
            _logger.info('last_date: %s', last_date)

            first_date = None
            if rec.banking_hours_start_date:
                first_date = datetime.datetime.strptime(str(rec.banking_hours_start_date), DFORMAT)
            _logger.info('first_date: %s', first_date)

            # total timesheet hours
            total = 0.0
            for hour_line in hour_lines:
                hour_line_date = datetime.datetime.strptime(str(hour_line.date), DFORMAT)
                if first_date and hour_line_date >= first_date and not hour_line.task_id.overtime:
                    total += hour_line.unit_amount
            _logger.info('total: %s', total)

            # total_contract_hours = (dates_count / 5) * int(contract_hours)
            total_contract_hours = 0.0
            if first_date and last_date and first_date <= last_date:
                total_contract_hours = (rec._calc_week_days(first_date, last_date) / 5) * rec.contract_hours
            _logger.info('total_contract_hours: %s', total_contract_hours)

            banked_hours = rec.banking_hours_amount
            if total and total_contract_hours:
                banked_hours += (total - total_contract_hours)
            _logger.info('banked_hours: %s', banked_hours)
            rec.banking_hours = banked_hours

    def _calc_week_days(self, first_date, last_date):
        # now = datetime.datetime.now()
        _logger.info('first_date: %s', first_date)
        delta = (last_date - first_date).days + 1
        _logger.info('delta: %s', delta)
        remainder = delta % 7
        _logger.info('remainder: %s', remainder)
        days = ((delta - remainder) / 7) * 5
        _logger.info('days: %s', days)
        remaining_day = first_date
        for i in range(remainder):
            _logger.info('remaining_day: %s', remaining_day)
            if remaining_day.weekday() != 5 and remaining_day.weekday() != 6:
                days += 1
            remaining_day += datetime.timedelta(days=1)
        _logger.info('(total)days: %s', days)
        return days

    @api.onchange('collaborator_id')
    def _compute_label(self):
        if self.collaborator_id:
            self.employee_label = self._get_label()
        else:
            self.employee_label = False

    def _get_label(self):
        get_company = int(self.collaborator_id[0])
        dict = {}
        for i in range(9):
            code = i + 1
            dict[code] = self.env['ir.config_parameter'].sudo().get_param('code_' + str(code))
        label = dict.get(get_company)
        return label


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    code_1 = fields.Char('1')
    code_2 = fields.Char('2')
    code_3 = fields.Char('3')
    code_4 = fields.Char('4')
    code_5 = fields.Char('5')
    code_6 = fields.Char('6')
    code_7 = fields.Char('7')
    code_8 = fields.Char('8')
    code_9 = fields.Char('9')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        for i in range(9):
            code = 'code_' + str(i + 1)
            self.env['ir.config_parameter'].sudo().set_param(code, getattr(self, code))

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        d = {}
        for i in range(9):
            code = 'code_' + str(i + 1)
            d[code] = self.env['ir.config_parameter'].sudo().get_param(code)
        res.update(d)
        return res
