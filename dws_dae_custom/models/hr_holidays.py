# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools
import datetime
import logging
import base64

_logger = logging.getLogger(__name__)

class HrHolidays(models.Model):
    _inherit = 'hr.leave.allocation'

    allocation_date = fields.Date('Allocation date')
    expiration_date = fields.Date('Expiration date')

    def _holiday_report(self):
        #report for the leaves what will expire in the near future
        allowed_holidays = self.env['hr.leave.allocation'].search([("expiration_date", ">=", datetime.datetime.now().strftime('%Y-%m-%d')),("expiration_date", "<", (datetime.date.today() + datetime.timedelta(2*365/12)).strftime('%Y-%m-%d')),
             ("allocation_date", "<=", datetime.datetime.now().strftime('%Y-%m-%d'))])

        if allowed_holidays:
            email_template = self.env.ref('dws_dae_custom.email_template_expiring_holiday')
            for allowed_holiday in allowed_holidays:
                employee = self.env['hr.employee'].sudo().search(
                    [('user_id.id', '=', allowed_holiday.employee_id.user_id.id)], limit=1)
                holiday_values = employee.calc_vac_hours(datetime.datetime.now().strftime('%Y-%m-%d'))

                if ((allowed_holiday.holiday_status_id.type == '1' and (
                    holiday_values['balance_ly'] - holiday_values['taken_cy']) > 0) or (
                        allowed_holiday.holiday_status_id.type == '2' and holiday_values['balance_ly_adv'] > 0) or (
                        allowed_holiday.holiday_status_id.type == '3' and holiday_values['balance_ly_all'] > 0)):

                    email_context = self.env.context.copy()
                    email_context.update({'email_to': 'anooteboom@daedalus.nl,ivboxtel@daedalus.nl,msteijger@daedalus.nl,Elise@dutchworld.nl','employee_name': allowed_holiday.employee_id.name})
#                    if employee.active == True:
#                        self.env['mail.template'].sudo().browse(email_template.id).with_context(email_context).send_mail(self.id)

        #report for the leaves for all employees
        contracts = self.env['hr.contract'].search([('state','=',"open")])
        columns = [u'Employee', u'Transport last year', u'Allocated this year', u'Balance this year', u'Transport last year above legal',
                   u'Allocated this year above legal', u'Balance this year above legal', u'Transport last year ADV', u'Allocated this year ADV', u'Balance this year ADV']

        csv = u','.join(columns)
        csv += "\n"
        if len(contracts) > 0:
            for contract in contracts:
                _logger.info('employee: %s', contract.employee_id)
                holiday_stats = contract.employee_id.calc_vac_hours(datetime.datetime.now().strftime('%Y-%m-%d'))
                employee = contract.employee_id.name
                if contract.employee_id.active == True:
                    csv_row = str(employee) + '","' + str(format(holiday_stats['balance_ly'], '.2f')).replace('.', ',') + '","' + str(format(holiday_stats['allocated_cy'], '.2f')).replace('.', ',') + '","' + str(format(holiday_stats['balance_cy'], '.2f')).replace('.', ',') + '","' + str(format(holiday_stats['balance_ly_all'], '.2f')).replace('.', ',') + '","' + str(format(holiday_stats['allocated_cy_all'], '.2f')).replace('.', ',') + '","' + str(format(holiday_stats['balance_cy_all'], '.2f')).replace('.', ',') + '","' + str(format(holiday_stats['balance_ly_adv'], '.2f')).replace('.', ',') + '","' + str(format(holiday_stats['allocated_cy_adv'], '.2f')).replace('.', ',') + '","' + str(format(holiday_stats['balance_cy_adv'], '.2f')).replace('.', ',')
                    csv += u"\"{}\"\n".format(csv_row)

        email_template = self.env.ref('dws_dae_custom.email_template_holiday_stats')
        attachment = {
            'name': 'holiday_stats-' + str(datetime.datetime.now().strftime('%Y-%m-%d')) + '.csv',
            'datas': base64.b64encode(csv.encode("utf-8")),
            'res_model': 'model_name',
            'type': 'binary'
        }

        id = self.env['ir.attachment'].create(attachment)

        email_context = self.env.context.copy()
        email_context.update({'email_to': 'msteijger@daedalus.nl,Elise@dutchworld.nl'})

        email_template.attachment_ids = [(4, id.id)]
        self.env['mail.template'].sudo().browse(email_template.id).with_context(email_context).send_mail(self.id)
        email_template.attachment_ids = [(3, id.id)]
        _logger.info('csv: %s', csv)