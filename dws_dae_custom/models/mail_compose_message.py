from odoo import fields,models,api,_

class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.model
    def generate_email_for_composer(self, template_id, res_ids, fields):
        """ Call email_template.generate_email(), get fields relevant for
            mail.compose.message, transform email_cc and email_to into partner_ids """
        multi_mode = True
        if isinstance(res_ids, int):
            multi_mode = False
            res_ids = [res_ids]

        returned_fields = fields + ['partner_ids', 'attachments']
        values = dict.fromkeys(res_ids, False)

        template_values = self.env['mail.template'].with_context(tpl_partners_only=True).browse(
            template_id).generate_email(res_ids, fields)

        for res_id in res_ids:
            res_id_values = dict((field, template_values[res_id][field]) for field in returned_fields if
                                 template_values[res_id].get(field))
            res_id_values['body'] = res_id_values.pop('body_html', '')

            # Change recipients email partner
            if template_values[res_id]['model'] == 'account.move':
                account_move_id = self.env['account.move'].browse(res_id)
                if account_move_id.partner_id.ubl_invoice or (
                        account_move_id.partner_id.parent_id and account_move_id.partner_id.parent_id.ubl_invoice):
                        partnerid = int(self.env['ir.config_parameter'].sudo().get_param('peppol_email'))
                        if partnerid:
                            res_id_values['partner_ids'] = [partnerid]

            values[res_id] = res_id_values

        return multi_mode and values or values[res_ids[0]]