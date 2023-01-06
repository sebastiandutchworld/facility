# -*- coding: utf-8 -*-

from odoo import api, models
from odoo.tools import pycompat
from odoo.tools import pdf
from odoo.exceptions import AccessError
import base64
import re

class MailTemplate(models.Model):
    _inherit = 'mail.template'

    def merge_attachments(self, model, id):
        Attachment = self.env['ir.attachment']
        attachments = Attachment.search([['res_model', '=', model], ['res_id', '=', id], ['type', '=', 'binary']])
        attachments = attachments.filtered(lambda rec: rec.name.endswith(".pdf"))
        if len(attachments) >= 2:
            try:
                merged_pdf = pdf.merge_pdf(attachments.mapped(lambda rec: base64.b64decode(rec.datas)))
                return base64.b64encode(merged_pdf)
            except AccessError:
                return False
        else:
            return False

    def generate_email(self, res_ids, fields=None):
        """ Method overridden in order to add an attachment containing the hours in approval report with the signature of the approver
        """
        print("in email send")
        rslt = super(MailTemplate, self).generate_email(res_ids, fields)

        multi_mode = True
        if isinstance(res_ids, int):
            res_ids = [res_ids]
            multi_mode = False

        #res_ids_to_templates = self.get_email_template(res_ids)
        for res_id in res_ids:
            related_model = self.env[self.model_id.model].browse(res_id)

            if related_model._name == 'account.move':
                attachments_list = multi_mode and rslt[res_id]['attachments'] or rslt['attachments']
                
                if related_model.approval_id:
                    attachments_list.append(('%s_%s_%s_approved.pdf' % (
                        related_model.approval_id.project_id.name.replace(" ", "_"), related_model.approval_id.sheet_id.startdate, related_model.approval_id.sheet_id.user_id.name.replace(" ", "_")), related_model.approval_id.pdf_report))
            
                #merge the PDF's if necessary
                if related_model.partner_id.pdf_merge or (related_model.partner_id.parent_id and related_model.partner_id.parent_id.pdf_merge):
                    merged = self.merge_attachments('account.move',related_model.id)
                    if merged:
                        # We need to treat both cases there because the assignment to the variable named attachments_list is detached from the original object
                        if multi_mode and rslt[res_id]['attachments']:
                            rslt[res_id]['attachments'] = []
                            rslt[res_id]['attachments'].append((str(re.sub('[!@#$/]', '',related_model.name)) + '.pdf', merged))
                            
                        else:
                            rslt['attachments'] = []
                            rslt['attachments'].append((str(re.sub('[!@#$/]', '',related_model.name)) + '.pdf', merged))
                            

                        # create the ubl attachment
                if related_model.partner_id.ubl_invoice or (related_model.partner_id.parent_id and related_model.partner_id.parent_id.ubl_invoice):
                    #We need to treat both cases there because the assignment to the variable named attachments_list is detached from the original object
                    if multi_mode and rslt[res_id]['attachments']:
                        #rslt[res_id]['attachments'].append(('Invoice_excel.xls', related_model.excel_invoice_template_create()))
                        rslt[res_id]['attachments'].append(('Invoice_ubl.xml', related_model.peppol_invoice_template_create(merged,str(re.sub('[!@#$/]', '',related_model.name)) + '.pdf')))
                    else:
                        #rslt['attachments'].append(('Invoice_excel.xls', related_model.excel_invoice_template_create()))
                        rslt['attachments'].append(('Invoice_ubl.xml', related_model.peppol_invoice_template_create(merged,str(re.sub('[!@#$/]', '',related_model.name)) + '.pdf')))

        return rslt