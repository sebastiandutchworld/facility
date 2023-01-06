from odoo import http
from odoo.http import request
from werkzeug.utils import redirect
import base64
import logging
_logger = logging.getLogger(__name__)


class WebsiteDocuments(http.Controller):
    @http.route('/my/documents', type='http', auth='user', website=True)
    def my_documents(self):
        # left as a comment, if we want to show all documents
        # documents = request.env['documents.document'].sudo().search([('owner_id', '=', request.env.user.id)])
        # get only documents created by user
        documents = request.env['documents.document'].sudo().search([('create_uid.id', '=', request.env.user.id)])
        payload = {
            'documents': documents
        }
        return request.render("dws_portal_documents.my_documents", payload)

    @http.route('/upload_document/', type='http', auth='public', methods=['POST'], multilang=False, csrf=False)
    def upload_document(self):
        attachments = self._attachments(request.params)
        result = self._insert_attachments(attachments)
        email_context = request.env.context.copy()
        email_context.update({
            'name': request.env.user.name,
        })

        template = request.env.ref('dws_portal_documents.email_template_document_upload')
        request.env['mail.template'].sudo().browse(template.id).with_context(email_context).send_mail(request.env.user.id)
        return redirect('/my/documents')

    # @http.route('/my/documents/download/<int:attachment_id>', type='http', auth='public', website=True)
    # def download_document(self, attachment_id):
    #     return redirect('/web/content/' + str(attachment_id) + '?download=true')

    @http.route('/my/documents/download/<int:attachment_id>', type='http', auth='public', website=True)
    def download_document(self, attachment_id):
        document = request.env['documents.document'].sudo().search([('attachment_id', '=', attachment_id)], limit=1)
        if request.env.user.id != document.create_uid.id:
            return None

        status, headers, content = request.env['ir.http'].sudo().binary_content(
            model='ir.attachment', id=attachment_id, field='datas', filename_field='name'
        )
        if status != 200:
            return request.env['ir.http'].sudo()._response_by_status(status, headers, content)
        else:
            content_base64 = base64.b64decode(content)
            headers.append(('Content-Length', len(content_base64)))
            response = request.make_response(content_base64, headers)
        return response

    @http.route('/my/documents/remove/<int:attachment_id>', type='http', auth='public', website=True)
    def remove_document(self, attachment_id):
        document = request.env['documents.document'].sudo().search([('attachment_id', '=', attachment_id)], limit=1)
        if request.env.user.id != document.create_uid.id:
            return None
        has_tag = False
        if document.tag_ids:
            has_tag = document.id
        else:
            document.unlink()
        documents = request.env['documents.document'].sudo().search([('create_uid.id', '=', request.env.user.id)])
        values = {
            'has_tag': has_tag,
            'documents': documents
        }
        return request.render("dws_portal_documents.my_documents",values)

    @staticmethod
    def _attachments(params):
        attachments = []
        for name, value in params.items():
            if hasattr(value, 'filename'):
                name = name.split('[', 1)[0]
                value.field_name = name
                attachments.append(value)
        return attachments

    @staticmethod
    def _insert_attachments(files):
        employee = request.env['hr.employee'].sudo().search([('user_id.id', 'in', [request.env.user.id])], limit=1)
        if not employee.id:
            return False

        for file in files:
            attachment_value = {
                'name': file.filename,
                'datas': base64.encodebytes(file.read()),
                'res_model': 'hr.employee',
                'res_id': employee.id
            }
            attachment_id = request.env['ir.attachment'].sudo().create(attachment_value)
            return True if isinstance(attachment_id, int) and attachment_id > 0 else False
