# -*- coding: utf-8 -*-

import datetime
import logging
import os

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class CronJobs(models.Model):
    _name = 'cron.jobs'

    def applicant_reminder(self):
        date_from = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
        applicants = self.env['hr.applicant'].search([('stage_id','=',False),('active','=',True),('create_date', '<=', date_from),('create_date', '>=', '2022-02-16')])
        for applicant in applicants:
            if applicant.cv_remainder_7_sent == False:
                print("send")
                email_context = self.env.context.copy()
                email_context.update({
                    'email_to': applicant.email_from
                })
                template = self.env.ref('dws_dae_recruitment.email_template_data_cv_reminder7')
                try:
                    self.env['mail.template'].sudo().browse(template.id).with_context(email_context).send_mail(applicant.id)
                    applicant.cv_remainder_7_sent = True
                except:
                    pass

        date_from = (datetime.datetime.now() - datetime.timedelta(days=14)).strftime('%Y-%m-%d')
        applicants = self.env['hr.applicant'].search(
            [('stage_id', '=', False), ('active', '=', True), ('create_date', '<=', date_from),('create_date', '>=', '2022-02-16')])
        for applicant in applicants:
            if applicant.cv_remainder_14_sent == False:
                email_context = self.env.context.copy()
                email_context.update({
                    'email_to': applicant.email_from
                })
                template = self.env.ref('dws_dae_recruitment.email_template_data_cv_reminder14')
                try:
                    self.env['mail.template'].sudo().browse(template.id).with_context(email_context).send_mail(applicant.id)
                    applicant.cv_remainder_14_sent = True
                except:
                    pass

        date_from = (datetime.datetime.now() - datetime.timedelta(days=21)).strftime('%Y-%m-%d')
        applicants = self.env['hr.applicant'].search(
            [('stage_id', '=', False), ('active', '=', True), ('create_date', '<=', date_from),('create_date', '>=', '2022-02-16')])
        for applicant in applicants:
            if applicant.cv_remainder_21_sent == False:
                email_context = self.env.context.copy()
                email_context.update({
                    'email_to': applicant.email_from
                })
                template = self.env.ref('dws_dae_recruitment.email_template_data_cv_reminder21')
                try:
                    self.env['mail.template'].sudo().browse(template.id).with_context(email_context).send_mail(applicant.id)
                    applicant.cv_remainder_21_sent = True
                except:
                    pass
        #Remove the records after 28 days
        date_from = (datetime.datetime.now() - datetime.timedelta(days=28)).strftime('%Y-%m-%d')
        applicants = self.env['hr.applicant'].search(
            [('stage_id', '=', False), ('active', '=', True), ('create_date', '<=', date_from)])

        for applicant in applicants:
            print("delete applicant: " + str(applicant.name))
            employee = self.env['hr.employee'].search(
            [('applicant_id', '=', applicant.id)],limit = 1)
            if employee:
                documents = self.env['documents.document'].sudo().search([('create_uid.id', '=', employee.user_id.id)])
                for document in documents:
                    if not document.tag_ids:
                        document.unlink()
                employee.user_id.unlink()
                employee.unlink()
                applicant.partner_id.unlink()
                applicant.unlink()
