# -*- coding: utf-8 -*-

import datetime, re
import logging
from odoo import models, fields, api, exceptions,_

_logger = logging.getLogger(__name__)

class DocumentCron(models.Model):
    _name = "document.cron"

    def document_actions(self):
        documents = self.env['documents.document'].search([])
        # pattern = '^(\d{3,6}).*'
        for doc in documents:
            # result = re.match(pattern, doc.name)
            # if result and result.group(1):
            #     print('it is an employee document')
            if doc.valid_until:
                date_deadline = doc.valid_until - datetime.timedelta(days=(30 * doc.signal_period_months))
                print(date_deadline)
                # add a tag when valid_until is set
                folder_id = self.env['documents.folder'].with_context(lang='en_US').search([('name', '=', 'HR')], limit=1)
                facet_id = self.env['documents.facet'].with_context(lang='en_US').search([('name', '=', 'Document Validate'), ('folder_id', '=', folder_id.id)], limit=1)
                print("folder id =", folder_id)
                print("facet id =", facet_id)
                tag_id = self.env['documents.tag'].with_context(lang='en_US').search([('name', '=', 'To Validate'), ('folder_id', '=', folder_id.id), ('facet_id', '=', facet_id.id)], limit=1)
                _logger.info('tag id: %s', tag_id.id)
                doc.tag_ids = [(4, tag_id[0].id)] if tag_id else [(0, 0, {'name': 'To Validate', 'facet_id': facet_id.id})]
                # add an activity
                if not doc.activity_created:
                    activity_type_id = self.env['mail.activity.type'].with_context(lang='en_US').search([('name', '=', 'Todo')], limit=1)
                    self.env['mail.activity'].create({
                        'res_id': doc.id,
                        'res_model_id': self.env['ir.model']._get('documents.document').id,
                        'activity_type_id': activity_type_id.id,
                        'summary': "Document " + doc.name + " needs to be renewed before " + datetime.date.strftime(doc.valid_until,'%Y-%m-%d'),
                        'user_id': 112, # Manuela
                        'date_deadline': date_deadline
                    })
                    doc.activity_created = True
                # send mail when signaling date is reached
                # if datetime.date.today() == date_deadline:
                #     email_context = self.env.context.copy()
                #     email_context.update({
                #         'email_to': 'hr-approver@daedalus.nl'
                #     })
                #     template = self.env.ref('dws_doc_management.email_template_document_renewal')
                #     self.env['mail.template'].sudo().browse(template.id).with_context(email_context).send_mail(doc.id)


    def conversion_actions(self):
        documents = self.env['documents.document'].search([])
        pattern = '^(\d{3,6}).*'
        for doc in documents:
            result = re.match(pattern, doc.name)
            if result and result.group(1):
                print('it is an employee document')
                # set employee document tag
                folder_id = self.env['documents.folder'].with_context(lang='en_US').search([('name', '=', 'HR')], limit=1)
                facet_id = self.env['documents.facet'].with_context(lang='en_US').search([('name', '=', 'Documents'), ('folder_id', '=', folder_id.id)], limit=1)

                tag_id = self.env['documents.tag'].with_context(lang='en_US').search([('name', '=', 'Employees Documents'), ('folder_id', '=', folder_id.id), ('facet_id', '=', facet_id.id)], limit=1)
                _logger.info('tag id: %s', tag_id.id)
                doc.tag_ids = [(4, tag_id[0].id)] if tag_id else [(0, 0, {'name': 'Employees Documents', 'facet_id': facet_id.id})]
                # doc.tag_ids = [(4, tag_id[0].id)] if tag_id else [(0, 0, {'name': 'Employees Documents'})]
                # set owner of document
                collaborator_id = result.group(1)

                if len(collaborator_id) == 3:
                    collaborator_id = "3" + collaborator_id

                self.env.cr.execute(
                    "select id from hr_employee where collaborator_id ~ '^" + collaborator_id + "' limit 1")
                employee = self.env['hr.employee'].sudo().browse([r['id'] for r in self.env.cr.dictfetchall()])
                second_search = False
                if not employee:
                    second_search = True
                    self.env.cr.execute(
                        "select id from hr_employee where collaborator_id ~ '\d{1,6}_" + collaborator_id + "' limit 1")
                    employee = self.env['hr.employee'].sudo().browse([r['id'] for r in self.env.cr.dictfetchall()])

                if employee:
                    doc.owner_id = employee.user_id.id
                _logger.info("second search = %s, collaborator id = %s, employee id = %s, name = %s and user_id = %s", second_search, (collaborator_id or 'empty'), (employee.id or 'empty'), (employee.name or 'empty'), (employee.user_id.id or 'empty'))
