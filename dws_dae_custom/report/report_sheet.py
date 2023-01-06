# -*- coding: utf-8 -*-

import datetime
import base64
from collections import OrderedDict
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DFORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTFORMAT
from odoo import api, models, fields,SUPERUSER_ID


class CustomDaedalusEmsReportSheet(models.AbstractModel):
    _name = 'report.dws_dae_custom.report_sheet'

    @api.model
    def _get_report_values(self, docids, data=None):
        res = {}

        approver = None
        if data['approver_id']:
            approver = self.env['res.partner'].sudo().search([('id', '=', data['approver_id'])])
        sheet = self.env['employee.sheet'].sudo().search([('id', '=', data['sheet_id'])])
        # pkr
        employee = self.env['hr.employee'].sudo().search([('user_id', '=', sheet.user_id.id)], limit=1)
        # /pkr
        # select all tasks for the sheet
        employee_hour_lines = self.env['employee.hours'].sudo().search([('employee_sheet_id', '=', sheet.id)])
        task_ids = []
        for hour_line in employee_hour_lines:
            if hour_line.task_id.id not in task_ids:
                task_ids.append(hour_line.task_id.id)
        # select all tasks for approver and tasks with hours
        if approver:
            approver_tasks = self.env['project.task'].sudo().search(['|', ('customer_contact', '=', approver.id), ('customer_contact2', '=', approver.id), ('id', 'in', task_ids), ('project_id', '=', data['project_id'].id)])
        else:
            approver_tasks = self.env['project.task'].sudo().search([('id', 'in', task_ids)])
        print('approver_tasks: ', approver_tasks)
        # if not approver_tasks:
        #     approver_tasks = self.env['project.task'].search(
        #         [('customer_contact2', '=', approver.id), ('id', 'in', task_ids)])

        # TODO TASKS NEED TO BE SELECTED ON OVERTIME=TRUE/FALSE
        # select hour_lines for approver tasks out of 'employee hour lines'
        hour_lines = [l for l in employee_hour_lines if l.task_id.id in approver_tasks.ids]

        # list with all tasks
        tasks = OrderedDict()
        count = 1
        for task in approver_tasks:
            name = "task" + str(count) + ": "
            tasks[name] = task.name
            count += 1

        # from all 'hour_lines' make a list with all dates only once
        dates = []
        for hour_line in hour_lines:
            if hour_line.date not in dates:
                dates.append(hour_line.date)

        # heads
        lines_head = []
        lines_head.append('Day')
        lines_head.append('Date')
        for i in range(len(approver_tasks)):
            task_name = "task" + str(i + 1)
            lines_head.append(task_name)

        # lines
        lines = []
        # for each date that has hours add a line
        for date in dates:
            day = datetime.datetime.strptime(str(date), DFORMAT).strftime('%A')
            count = 1
            line = []
            line.append(day)
            line.append(date)
            for task in approver_tasks:
                task_value = ''
                task_regular_str = ''
                from_time = ''
                to_time = ''
                for hour_line in hour_lines:
                    if hour_line.task_id.id == task.id and hour_line.date == date and hour_line.regular:
                        task_regular = hour_line.regular
                        task_from = ''
                        task_to = ''
                        # get hour lines containing from and to time for regular hours
                        hour_line_regular_task_id = hour_line.task_id
                        hour_line_regular_date = hour_line.date
                        for hour_line in hour_lines:
                            if hour_line.task_id == hour_line_regular_task_id and hour_line.date == hour_line_regular_date:
                                if hour_line.fromtime != False:
                                    task_from = hour_line.fromtime
                                if hour_line.totime != False:
                                    task_to = hour_line.totime
                        from_time = '  '
                        to_time = '  '
                        if task_from:
                            from_time = str(datetime.datetime.strptime(str(task_from), DTFORMAT).strftime('%H:%M'))
                        if task_to:
                            to_time = str(datetime.datetime.strptime(str(task_to), DTFORMAT).strftime('%H:%M'))
                        task_regular_str = str(task_regular)
                task_value = task_regular_str + ' -- ' + from_time + '-' + to_time
                line.append(task_value)
            lines.append(line)
            count += 1
        # add a line with task totals
        task_totals = ['Total: ', '']
        for task in approver_tasks:
            # task_hour_lines = self.env['employee.hours'].search([('employee_sheet_id', '=', sheet.id), ('task_id', '=', task.id)])
            task_hour_lines = [l for l in employee_hour_lines if l.task_id.id == task.id]
            task_total = 0
            for task_hour_line in task_hour_lines:
                task_total += task_hour_line.regular
            task_totals.append(task_total)
        lines.append(task_totals)

        res['employee'] = employee
        res['period_start'] = sheet.startdate
        res['approver'] = approver
        res['tasks'] = tasks
        res['lines_head'] = lines_head
        res['lines'] = lines
        res['imgbase64'] = data['imgbase64']
        res['employee_id'] = data['employee_id']
        res['company'] = data['project_id'].sale_line_id.order_id.company_id
        print(res)
        print(data)

        report = self.env['ir.actions.report'].with_user(SUPERUSER_ID)._get_report_from_name('dws_dae_custom.report_sheet')
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': self.env[report.model].browse(docids),
            'result': res,
        }
        return docargs