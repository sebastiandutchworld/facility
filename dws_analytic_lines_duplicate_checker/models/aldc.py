from odoo import models, fields, api
from datetime import date, timedelta
from collections import Counter

import logging
_logger = logging.getLogger(__name__)


class Line:
    employee_id = None
    employee_name = None
    project_id = None
    project_name = None
    task_id = None
    task_name = None
    hours = None
    # description = None

    def __init__(self, analytic_line):
        self.employee_id = analytic_line.employee_id if analytic_line.employee_id else 0
        self.employee_name = analytic_line.employee_id.name or ''
        self.project_id = analytic_line.project_id if analytic_line.project_id else 0
        self.project_name = analytic_line.project_id.name or ''
        self.task_id = analytic_line.task_id if analytic_line.task_id else 0
        self.task_name = analytic_line.task_id.name or ''
        self.hours = analytic_line.unit_amount
        # self.description = analytic_line.name

    # Duplicate definition (from the task description)
    # Same task, same project, same date, same time
    # But it needs to be applied only if the line is for the same employee, so employee is added too
    # Date doesn't need to be compared, since the lines will be only for a specific day (the day when the cron runs)
    # First condition (employee_id !=0) is there to avoid comparison with lines that came from somewhere else
    def __eq__(self, other):
        return (self.employee_id != 0 and
                self.employee_id == other.employee_id and
                self.project_id == other.project_id and
                self.task_id == other.task_id and
                self.hours == other.hours)

    def __hash__(self):
        return hash(('employee_id', self.employee_id,
                     'project_id', self.project_id,
                     'task_id', self.task_id,
                     'hours', self.hours))


class DuplicateCheckerCron(models.Model):
    _name = 'aldc'

    def mail_duplicate_lines_notification(self, duplicates):
        email_context = self.env.context.copy()
        email_context.update({
            'duplicates': duplicates,
        })

        template = self.env.ref('dws_analytic_lines_duplicate_checker.email_duplicate_analytic_lines_notification')
        self.env['mail.template'].sudo().browse(template.id).with_context(email_context).send_mail(0)

    def duplicate_checker(self):
        today = date.today()
        check_day = today - timedelta(days=1)
        analytic_lines = self.env['account.analytic.line'].sudo().search([('date', '=', check_day)])
        lines = list(map(lambda analytic_line: Line(analytic_line), analytic_lines))

        duplicates = []
        count = Counter(lines)
        for line in count:
            if count[line] > 1:
                duplicate = (str(count[line]) + ' times: ' + line.employee_name + ' - ' + line.project_name +
                             ' - ' + line.task_name + ' - ' + str(line.hours) + ' hours')
                duplicates.append(duplicate)
        if len(duplicates) > 0:
            self.mail_duplicate_lines_notification(duplicates)
