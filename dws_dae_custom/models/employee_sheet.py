# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools
import datetime
import logging
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DFORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTFORMAT
import math

_logger = logging.getLogger(__name__)

class EmployeeSheet(models.Model):
    _name = 'employee.sheet'
    #_inherit = ['mail.thread', 'resource.mixin']
    _rec_name = 'user_id'

    user_id = fields.Many2one('res.users', string='User')
    employee = fields.Many2one('hr.employee', compute='get_employee', store=True)
    employee_company = fields.Many2one(related='employee.company_id', string='Employee Company')
    #company_id = fields.Many2one(related='employee.company_id', string='Employee Company')
    #company_id = fields.Many2one('res.company', compute='get_company')
    startdate = fields.Date("Startdate")
    enddate = fields.Date("Enddate")

    status = fields.Selection([('0', 'Todo'),('1', 'Confirmed by employee'), ('2', 'Approved by BO'),
                               ('3', 'Approved by customers'), ('4', 'Approved by all customers'),('5','Invoiced')])

    notes = fields.Char("Notes")
    hour_ids = fields.One2many('employee.sheet.hours', 'employee_sheet_id', string='Hours')

    @api.model
    def schedule_timesheet_reminder(self):
        # nrdays = 2
        nrdays = int(self.env['ir.config_parameter'].sudo().get_param('employee_timesheet_reminder_interval'))
        # print('nrdays=', nrdays)
        # email_context = self.env.context.copy()
        read_contracts = self.env['hr.contract'].sudo().read_group([], ['employee_id'], ['employee_id'])
        # print('read contracts=', read_contracts)
        active_employee_ids = []
        for data in read_contracts:
            if data['employee_id']:
                active_employee_ids.append(data['employee_id'][0])
        # print('active ids=', active_employee_ids)
        sheet_ids = self.search([
            ('enddate', '<=', fields.Datetime.to_string(datetime.datetime.today() - datetime.timedelta(days=nrdays))),
            ('employee.id', 'in', active_employee_ids),
            ('status', '=', 0)
            ])
        # print('today=', fields.Datetime.to_string(datetime.datetime.today()))
        # print('delta=', datetime.timedelta(days=nrdays))
        # print('date=', fields.Datetime.to_string(datetime.datetime.today() - datetime.timedelta(days=nrdays)))
        # print('sheet ids=', sheet_ids)
        reminder_ids = []
        if (sheet_ids):
            for sheet in sheet_ids:
                print('sheet ids=', sheet_ids)
                contracts = self.env['hr.contract'].search([('employee_id', '=', sheet.employee.id)])
                if self.overlap_periods(sheet, contracts):
                    reminder_ids.append(sheet.id)
                    # email_context.update({
                    #     'email_to': sheet.employee.user_id.partner_id.email,
                    #     'sheet': sheet,
                    #     'employee': sheet.employee
                    # })
                    #
                    # template = self.env.ref('daedalus_ems.email_template_data_timesheet_reminder')
                    # self.env['mail.template'].sudo().browse(template.id).with_context(email_context).send_mail(sheet.id)
        self.mail_employee_timesheet_reminders(reminder_ids)

    def mail_employee_timesheet_reminders(self, sheet_ids):
        sheets = self.search([('id', 'in', sheet_ids)])
        email_context = self.env.context.copy()
        for sheet in sheets:
            email_context.update({
                'email_to': sheet.employee.user_id.partner_id.email,
                'sheet': sheet,
                'employee': sheet.employee
            })

            template = self.env.ref('dws_dae_custom.email_template_data_timesheet_reminder')
            self.env['mail.template'].sudo().browse(template.id).with_context(email_context).send_mail(sheet.id)

    def button_action_employee_timesheet_reminder(self):
        print('you pushed a button')
        active_ids = self.env.context.get('active_ids', []) or []
        print('active ids=', active_ids)
        self.mail_employee_timesheet_reminders(active_ids)

    def overlap_periods(self, sheet, contracts):
        overlap = False
        # print('sheet=', sheet)
        # print('contracts=', contracts)
        for contract in contracts:
            # iterate over sheet dates
            # print('for loop')
            for date in self.date_range(fields.Date.from_string(sheet.startdate), fields.Date.from_string(sheet.enddate)):
                # iterate over contract dates
                # print('date=', date)
                # print('sheet date loop')
                if date in self.date_range(fields.Date.from_string(contract.date_start), (fields.Date.from_string(contract.date_end) or datetime.date.today())):
                    # print('date in contract period')
                    overlap = True
        return overlap

    def date_range(self, date1, date2):
        # print('date1=', date1)
        # print('date2=', date2)
        for n in range(int((date2 - date1).days) + 1):
            yield date1 + datetime.timedelta(n)

    @api.depends('user_id')
    def get_company(self):
        for rec in self:
            rec.company_id = rec.employee.company_id

    @api.depends('user_id')
    def get_employee(self):
        for rec in self:
            rec.employee = rec.env['hr.employee'].sudo().search([('user_id', '=', rec.user_id.id)], limit=1)

    def get_involved_contacts(self, uid):
        contacts1 = []
        contacts2 = []
        contacts1_projects = []
        contacts2_projects = []
        task_search = self.env['project.task'].sudo().search([
            ('user_ids', 'in', [uid]), ('planned_date_begin', "<=", self.enddate),
            ('planned_date_end', ">=", self.startdate)
        ])
        print(task_search)
        for task in task_search:
            #print(task.customer_contact)
            if task.customer_contact and task.project_id.id not in contacts1_projects:
               contacts1_projects.append(task.project_id.id)
               contacts1.append({"project_id":task.project_id.id,"contact":task.customer_contact})
            if task.customer_contact2 and task.project_id.id not in contacts2_projects:
                contacts2_projects.append(task.project_id.id)
                contacts2.append({"project_id":task.project_id.id,"contact":task.customer_contact2})
        contacts = [contacts1,contacts2]
        return contacts

    # def get_periods(self):
    #     periods = [('2018-01-01', '2018-01-28'),
    #                ('2018-01-29', '2018-02-25'),
    #                ('2018-02-26', '2018-03-25'),
    #                ('2018-03-26', '2018-04-22'),
    #                ('2018-04-23', '2018-05-20'),
    #                ('2018-05-21', '2018-06-17'),
    #                ('2018-06-18', '2018-07-15'),
    #                ('2018-07-16', '2018-08-12'),
    #                ('2018-08-13', '2018-09-09'),
    #                ('2018-09-10', '2018-10-07'),
    #                ('2018-10-08', '2018-11-04'),
    #                ('2018-11-05', '2018-12-02'),
    #                ('2018-12-03', '2018-12-30'),
    #                ('2018-12-31', '2019-01-27'),
    #                ('2019-01-28', '2019-02-24'),
    #                ('2019-02-25', '2019-03-24'),
    #                ('2019-03-25', '2019-04-21'),
    #                ('2019-04-22', '2019-05-19'),
    #                ('2019-05-20', '2019-06-16'),
    #                ('2019-06-17', '2019-07-14'),
    #                ('2019-07-15', '2019-08-11'),
    #                ('2019-08-12', '2019-09-08'),
    #                ('2019-09-09', '2019-10-06'),
    #                ('2019-10-07', '2019-11-03'),
    #                ('2019-11-04', '2019-12-01'),
    #                ('2019-12-02', '2019-12-29'),
    #                ('2019-12-30', '2020-01-26'),
    #                ('2020-01-27', '2020-02-23'),
    #                ('2020-02-24', '2020-03-22'),
    #                ('2020-03-23', '2020-04-19'),
    #                ('2020-04-20', '2020-05-17'),
    #                ('2020-05-18', '2020-06-14'),
    #                ('2020-06-15', '2020-07-12'),
    #                ('2020-07-13', '2020-08-09'),
    #                ('2020-08-10', '2020-09-06'),
    #                ('2020-09-07', '2020-10-04'),
    #                ('2020-10-05', '2020-11-01'),
    #                ('2020-11-02', '2020-11-29'),
    #                ('2020-11-30', '2020-12-27')
    #                ]
    #     return periods

    def get_holidays(self):
        #holidays applicable to everyone is hardcoded here
        holidays = ['2018-01-01','2018-04-01','2018-04-02','2018-04-27','2018-05-10','2018-05-20','2018-05-21','2018-12-25','2018-12-26',
                    '2019-01-01','2019-04-19','2019-04-22','2019-04-27','2019-05-05','2019-05-30','2019-06-10','2019-12-25','2019-12-26',
                    '2020-01-01','2020-04-13','2020-04-27','2020-05-05','2020-05-21','2020-06-01','2020-12-25','2020-12-26','2021-01-01',
                    '2021-04-02','2021-04-04','2021-04-05','2021-04-27','2021-05-05','2021-05-13','2021-05-23','2021-05-24','2021-12-25',
                    '2021-12-26'
                    ]

        return holidays

    def get_task_holidays(self,tasks):
        # special holidays and working days per project

        special_days = {}
        for task in tasks:
            holidays = []
            workdays = []

            # special_days_task = {holidays,workdays}
            # special_days.append(task.id)
            holiday_search = self.env['project.holidaysets'].sudo().search([
                ('project_id', '=', task.project_id.id)])
            print(holiday_search)
            if holiday_search:
                for special_day in holiday_search:
                    if special_day.type == '0':
                        holidays.append(str(datetime.datetime.strptime(str(special_day.date), DFORMAT).strftime('%Y-%m-%d')))
                    else:
                        workdays.append(str(datetime.datetime.strptime(str(special_day.date), DFORMAT).strftime('%Y-%m-%d')))

            special_days.update({task.id: {"holidays": holidays,"workdays":workdays}})

        return special_days

    def verify_approval_status(self):
        sheet_approvals = self.env['employee_sheet.approvals'].sudo().search(
            [('sheet_id', '=', self.id), '|',('status', '!=', '1'),('status','=',False)])
        #if we cannot find any approvals with status other than 1 then we can start transferring the hours
        if not sheet_approvals:
            self.transfer_hours()
            self.write(({'status': '4'}))


    def transfer_hours(self):
        analytic_line = self.env['account.analytic.line']
        employee = self.env['hr.employee'].sudo().search([('user_id', '=', self.user_id.id)], limit=1)
        # #transfer regular hours
        # hours = self.env['employee.hours'].sudo().search([('employee_sheet_id', '=', self.id), ('regular', '!=', "")])
        # for hour in hours:
        #     analytic_line.sudo().create({
        #         'partner_id': self.user_id.partner_id.id,
        #         'user_id': self.user_id.id,
        #         'project_id': hour.task_id.project_id.id,
        #         'task_id': hour.task_id.id,
        #         'account_id': hour.task_id.project_id.analytic_account_id.id,
        #         'date': hour.date,
        #         'unit_amount': hour.regular,
        #         'employee_id': employee.id or ""
        #     });
        #
        # #transfer other hours
        task_mappings = {}
        task_mappings['project_other_hours'] = self.user_id.company_id.project_other_hours.id
        task_mappings['task_vacation'] = self.user_id.company_id.task_vacation.id
        task_mappings['task_adv'] = self.user_id.company_id.task_adv.id
        task_mappings['task_illness'] = self.user_id.company_id.task_illness.id
        task_mappings['task_nw'] = self.user_id.company_id.task_nw.id
        task_mappings['task_all'] = self.user_id.company_id.task_all.id
        hours = self.env['employee.hours'].sudo().search([('employee_sheet_id', '=', self.id), '|','|','|','|',('regular', '!=', ""),('vacation', '!=', ""),('adv', '!=', ""),('illness', '!=', ""),('nw', '!=', "")])
        for hour in hours:
            hourval = False
            hourval2 = False
            taskid2 = False
            if hour.vacation:
                if not task_mappings['task_vacation'] or not task_mappings['project_other_hours']:
                    continue

                if hour.vacation <= math.floor(employee.calc_vac_hours(hour.date)["balance_cy"]):
                    taskid = task_mappings['task_vacation']
                    hourval = hour.vacation
                else:
                    if employee.calc_vac_hours(hour.date)["balance_cy"] > 0:
                        taskid = task_mappings['task_vacation']
                        hourval = math.floor(employee.calc_vac_hours(hour.date)["balance_cy"])

                    taskid2 = task_mappings['task_all']
                    hourval2 = hour.vacation - math.floor(employee.calc_vac_hours(hour.date)["balance_cy"])

                projectid = task_mappings['project_other_hours']
                name = False
            if hour.adv:
                if not task_mappings['task_adv'] or not task_mappings['project_other_hours']:
                    continue
                hourval = hour.adv
                taskid = task_mappings['task_adv']
                projectid = task_mappings['project_other_hours']
                name = False
            if hour.illness:
                if not task_mappings['task_illness'] or not task_mappings['project_other_hours']:
                    continue
                hourval = hour.illness
                taskid = task_mappings['task_illness']
                projectid = task_mappings['project_other_hours']
                name = False
            if hour.nw:
                if not task_mappings['task_nw'] or not task_mappings['project_other_hours']:
                    continue
                hourval = hour.nw
                taskid = task_mappings['task_nw']
                projectid = task_mappings['project_other_hours']
                name = False
            if hour.regular:
                hourval = hour.regular
                taskid = hour.task_id.id
                projectid = hour.task_id.project_id.id
                name = False

                fromtohours = self.env['employee.hours'].sudo().search(
                [('employee_sheet_id', '=', self.id),('task_id','=',hour.task_id.id),('date','=',hour.date),'|',('fromtime', '!=', False),('totime', '!=', False)])

                fromstring = ""
                tostring = ""
                for fromtohour in fromtohours:
                    if fromtohour.fromtime:
                        fromstring = "From: " + str(datetime.datetime.strptime(str(fromtohour.fromtime), DTFORMAT).strftime('%H:%M'))
                    if fromtohour.totime:
                        tostring = "To: " + str(datetime.datetime.strptime(str(fromtohour.totime), DTFORMAT).strftime('%H:%M'))

                if fromstring != "" and tostring != "":
                    name = fromstring + ' - ' + tostring

            project = self.env['project.project'].sudo().browse(projectid)

            duplicate_line = False

            # check for a duplicate analytic line
            if hourval:
                duplicate_line = analytic_line.sudo().search([
                    ('date', '=', hour.date),
                    ('employee_id', '=', employee.id),
                    ('project_id', '=', projectid),
                    ('task_id', '=', taskid),
                    ('unit_amount', '=', hourval),
                    ], limit=1)
            if hourval2:
                duplicate_line = analytic_line.sudo().search([
                    ('date', '=', hour.date),
                    ('employee_id', '=', employee.id),
                    ('project_id', '=', projectid),
                    ('task_id', '=', taskid2),
                    ('unit_amount', '=', hourval2),
                    ], limit=1)

            if duplicate_line:
                _logger.info('duplicate analytic lines detected')
            # write analytic line, but only if there isn't a duplicate
            else:
                if hourval:
                    analytic_line.sudo().create({
                        'partner_id': self.user_id.partner_id.id,
                        'user_id': self.user_id.id,
                        'project_id': projectid,
                        'task_id': taskid,
                        'account_id': project.analytic_account_id.id,
                        'company_id': project.analytic_account_id.company_id.id,
                        'date': hour.date,
                        'unit_amount': hourval,
                        'employee_id': employee.id or "",
                        'name': name
                    })

                if hourval2:
                    analytic_line.sudo().create({
                        'partner_id': self.user_id.partner_id.id,
                        'user_id': self.user_id.id,
                        'project_id': projectid,
                        'task_id': taskid2,
                        'account_id': project.analytic_account_id.id,
                        'company_id': project.analytic_account_id.company_id.id,
                        'date': hour.date,
                        'unit_amount': hourval2,
                        'employee_id': employee.id or "",
                        'name': name
                    })

            self.env.cr.commit()

    def get_periods(self):
        start_date = datetime.datetime.strptime('2018-01-01','%Y-%m-%d')
        periods = []
        while len(periods) < 14:
            # if 31-12-xxxx is in week 53 add an extra week to the period containing 31-12-xxxx
            # exclude years before 2021 and add an extra 5 week period starting 3021-01-25
            year_has_week_53 = (53 == datetime.date(start_date.year, 12, 31).isocalendar()[:2][1])
            period_has_31_dec = ((datetime.date(start_date.year, 12, 31) - start_date.date()).days < 28)
            if (start_date.date() == datetime.date(2021, 1, 25) or (year_has_week_53 and period_has_31_dec)) and start_date.date() > datetime.date(2021, 1, 1):
                # print('period with 5 weeks =', start_date)
                period = (datetime.datetime.strftime(start_date, '%Y-%m-%d'), datetime.datetime.strftime(
                    (start_date + datetime.timedelta(weeks=5) - datetime.timedelta(days=1)), '%Y-%m-%d'))
                start_date += datetime.timedelta(weeks=5)
            else:
                period = (datetime.datetime.strftime(start_date,'%Y-%m-%d'), datetime.datetime.strftime((start_date + datetime.timedelta(weeks=4) - datetime.timedelta(days=1)),'%Y-%m-%d'))
                start_date += datetime.timedelta(weeks=4)
            if (datetime.datetime.strptime(str(period[1]), '%Y-%m-%d') + datetime.timedelta(weeks=5)).date() > datetime.date.today():
                periods.append(period)
        return periods


    def generate_timesheets(self,user_id):
        # does give periods from current date till ... -> make 13 periods from now...
        # periods = self.get_periods_from_last_month(self.get_periods())
        # print('periods1=', periods)
        # print('periods2=', self.get_periods2())
        periods = self.get_periods()
        employee = self.env['hr.employee'].search([('user_id', '=', user_id)], limit=1)
        contract = self.env['hr.contract'].search([('employee_id', '=', employee.id), ('state', '=', 'open')], limit=1)
        if contract:
            for period in periods:
                if not contract.date_end or contract.date_end > datetime.datetime.strptime(str(period[0]), '%Y-%m-%d').date():
                    sheet = self.search([('user_id', '=', user_id), ('startdate', '=', period[0]),('enddate', '=', period[1])])
                    if not sheet:
                        self.create({
                            'user_id': user_id,
                            'startdate': period[0],
                            'enddate': period[1],
                            'status': "0"
                        })
        return True

    # def get_periods_from_last_month(self, periods):
    #     current_date = datetime.date.today()
    #     remaining_periods = []
    #     for period in periods:
    #         if (fields.Date.from_string(period[1]) + datetime.timedelta(days=28)) > current_date:
    #             remaining_periods.append(period)
    #     return remaining_periods

class EmployeeSheetHours(models.Model):
    _name = 'employee.sheet.hours'
    _auto = False

    task_id = fields.Many2one('project.task')
    date = fields.Date()
    fromtime = fields.Char('From')
    totime = fields.Char('To')
    regular = fields.Float()
    vacation = fields.Float()
    adv = fields.Float()
    illness = fields.Float()
    nw = fields.Float()
    employee_sheet_id = fields.Many2one('employee.sheet')

    #@api.model_cr  # cr #deprecated function
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE OR REPLACE VIEW %s AS
        (SELECT ROW_NUMBER() OVER (ORDER BY date, task_id, employee_sheet_id) AS id,
                 employee_sheet_id,
                 task_id,
                 date,
                 string_agg(to_char(fromtime, 'HH24:MI'),'') AS fromtime,
                 string_agg(to_char(totime, 'HH24:MI'),'') AS totime,
                 max(regular) AS regular,
                 max(vacation) AS vacation,
                 max(adv) AS adv,
                 max(illness) AS illness,
                 max(nw) AS nw
        FROM employee_hours
        GROUP BY date, task_id, employee_sheet_id)""" % (self._table,))