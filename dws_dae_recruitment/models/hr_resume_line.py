# See LICENSE file for full copyright and licensing details.

import random
from odoo import api, fields, models, _,SUPERUSER_ID
from datetime import datetime, time
from odoo.tools import float_compare
from odoo.tools.float_utils import float_round
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.exceptions import AccessDenied


class ResumeLineType(models.Model):
    _inherit = "hr.resume.line.type"

    mandatory = fields.Boolean("Mandatory",default=False)
    display_type = fields.Selection([('classic', 'Classic'), ('study', 'Study'), ('experience', 'Experience'),('language', 'Language'),('cert','Certificate')],
                                    default='classic')

class EmpPortalResume(models.Model):
    _inherit = "hr.resume.line"

    aircraft_type = fields.Char("Aircraft type")
    company = fields.Char("Company")
    row_display_type = fields.Selection(
        [('classic', 'Classic'), ('study', 'Study'), ('experience', 'Experience'), ('language', 'Language'),
         ('cert', 'Certificate')],
        related='line_type_id.display_type',readonly=True)
    graduated_on_date = fields.Date('Graduated on')
    date_start = fields.Date(required=False)
    from_portal = fields.Boolean("Entry from portal")

    def _compute_display_type(self):
        for line in self:
            line.row_display_type = line.line_type_id.display_type

    def create(self, vals_list):
        if "from_portal" in vals_list: #allow creation only from portal
            res = super(EmpPortalResume, self).create(vals_list)
            return res

    def write(self, vals_list):
        if "from_portal" in vals_list: #allow creation only from portal
             res = super(EmpPortalResume, self).write(vals_list)
             return res

    def validate_data(self,values):
        if 'line_type_id' not in values:
            values['line_type_id'] = values['line_type']
        if values['line_type_id']:
            line_type = self.env['hr.resume.line.type'].sudo().browse(int(values['line_type_id']))
            print(line_type)
            if line_type[0].display_type == "study":
                #values['date_start'] = values['date_end']
                if not (values['name'] and values['line_type_id'] and values['date_start']):
                    return {
                        'errors': _('Some fields are required !')
                    }
            elif line_type[0].display_type == "experience":
                if not (values['name'] and values['company'] and values['date_start']):
                    return {
                        'errors': _('Some fields are required !')
                    }
            elif line_type[0].display_type == "language":
                if not (values['description']):
                    return {
                        'errors': _('Some fields are required !')
                    }
            elif line_type[0].display_type == "cert":
                if not (values['name'] and values['date_start']):
                    return {
                        'errors': _('Some fields are required !')
                    }
            else:
                if not (values['name'] and values['date_start'] and values['date_end']):
                    return {
                        'errors': _('Some fields are required !')
                    }
        else:
            if not (values['name'] and values['date_start'] and values['date_end']):
                return {
                    'errors': _('Some fields are required !')
                }

        return True

    @api.model
    def create_resume_line(self, values):
        employee = self.env['hr.employee'].sudo().search(
            [('user_id.id', 'in', [self.env.user.id])], limit=1)
        if not (employee):
            raise AccessDenied()
        user = self.env.user
        self = self.sudo()

        if values['date_start']:
            values['date_start'] = values['date_start'].lstrip('0') + "-01"
            try:
                datetime.strptime(values['date_start'], DF)
            except ValueError as e:
                return {
                    'errors': _('Date format is invalid for start date!')
                }
        if values['date_end']:
            values['date_end'] = values['date_end'].lstrip('0') + "-01"
            try:
                datetime.strptime(values['date_end'], DF)
            except ValueError:
                return {
                    'errors': _('Date format is invalid for end date!')
                }
        if values['graduated_on_date']:
            values['graduated_on_date'] = values['graduated_on_date'].lstrip('0') + "-01"
            try:
                datetime.strptime(values['graduated_on_date'], DF)
            except ValueError:
                return {
                    'errors': _('Date format is invalid for graduated date!')
                }
        valid = self.validate_data(values)
        if valid != True:
            return valid
        else:
            values = {
                'name': values['name'],
                'line_type_id': int(values['line_type_id']),
                'date_start': values['date_start'] or False,
                'date_end': values['date_end'] or False,
                'graduated_on_date': values['graduated_on_date'] or False,
                'description': values['description'],
                'employee_id': values['employee_id'],
                'aircraft_type': values['aircraft_type'],
                'company': values['company'],
                'from_portal': True
            }
            myline = self.env['hr.resume.line'].sudo().create(values)
            #self.check_completeness(values['employee_id'])
            return {
                'id': myline.id
            }

    def unlink(self):
        rec = super(EmpPortalResume, self).unlink()
        return rec

    @api.model
    def check_completeness(self,values):
        mandatory_lines = self.env['hr.resume.line.type'].sudo().search([('mandatory', '=', True)])
        lines = self.env['hr.resume.line'].read_group(
            [('employee_id', '=', int(values['employee_id'])),
             ('line_type_id', 'in', mandatory_lines.ids)],
            ['line_type_id'], ['line_type_id'])

        if len(mandatory_lines) == len(lines):
            application = self.env['hr.applicant'].sudo().search([('emp_id', '=', int(values['employee_id']))])
            if application and not application.stage_id:
                application.with_user(SUPERUSER_ID).write({'stage_id':1})
            else:
                email_context = self.env.context.copy()
                employee = self.env['hr.employee'].sudo().browse(int(values['employee_id']))
                hr_contact = self.env['res.partner'].sudo().browse(
                    [int(self.env['ir.config_parameter'].sudo().get_param('hr_approver_partner'))])
                recruitment_contact = self.env['res.partner'].sudo().search([('name', '=', 'HR Recruitment')], limit=1)

                #send mail for hr approver
                email_context.update({'email_to': hr_contact.email,'employee_name':employee.name})
                email_template = self.env.ref('dws_dae_recruitment.email_template_data_cv_sent_in')
                self.env['mail.template'].sudo().browse(email_template.id).with_context(email_context).send_mail(
                    self.id)
                #sed mail to the applicant
                email_context = self.env.context.copy()
                email_context.update({'email_to': employee.work_email, 'employee_name': employee.name})
                email_template = self.env.ref('dws_dae_recruitment.email_template_data_cv_sent_in_employee')
                self.env['mail.template'].sudo().browse(email_template.id).with_context(email_context).send_mail(
                    self.id)

                # send mail for recruitment inbox
                email_context = self.env.context.copy()
                email_context.update({'email_to': recruitment_contact.email, 'employee_name': employee.name})
                email_template_recruitment = self.env.ref('dws_dae_recruitment.email_template_data_cv_sent_in_recruitment')
                self.env['mail.template'].sudo().browse(email_template_recruitment.id).with_context(email_context).send_mail(self.id)


            return "True"
            # else:
            #     if application.stage_id.id == 1:
            #         application.stage_id = False

        return "False"

    @api.model
    def update_resume_portal(self, values):
        if 'aircraft_type' not in values:
            values['aircraft_type'] = ''
        if 'company' not in values:
            values['company'] = ''
        if 'name' not in values:
            values['name'] = ''
        valid = self.validate_data(values)
        grad_date = False
        dt_from = False
        dt_to = False

        if valid != True:
            return valid
        else:
            if 'date_start' in values:
                if values['date_start'] != '':
                    values['date_start'] = values['date_start'] + "-01"
                    dt_from = datetime.strptime(values['date_start'], DF).date()
            if 'date_end' in values:
                if values['date_end'] != '':
                    values['date_end'] = values['date_end'] + "-01"
                    dt_to = datetime.strptime(values['date_end'], DF).date()
            if 'graduated_on_date' in values:
                if values['graduated_on_date'] != '':
                    values['graduated_on_date'] = values['graduated_on_date'] + "-01"
                    grad_date = datetime.strptime(values['graduated_on_date'], DF).date()



            skill_values = {
                'name': values['name'],
                'line_type_id': int(values['line_type']),
                'date_start': dt_from,
                'date_end': dt_to,
                'description': values['description'],
                'aircraft_type': values['aircraft_type'],
                'company': values['company'],
                'graduated_on_date': grad_date,
                'from_portal': True
            }
            if values['skillID']:
                skill_rec = self.env['hr.resume.line'].sudo().browse(values['skillID'])
                print(skill_rec)
                if skill_rec:
                    skill_rec.sudo().write(skill_values)
            return {
                'id': values['skillID']
            }