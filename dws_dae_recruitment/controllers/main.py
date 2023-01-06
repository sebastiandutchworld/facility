# See LICENSE file for full copyright and licensing details

from operator import itemgetter
from odoo import fields
from odoo import http
from odoo.http import request
from odoo.tools import date_utils, groupby as groupbyelem
from odoo.tools.translate import _
from odoo.addons.website.controllers.form import WebsiteForm
import json
import logging
from psycopg2 import IntegrityError
from odoo.exceptions import ValidationError, UserError
_logger = logging.getLogger(__name__)


class WebsiteFormInherit(WebsiteForm):

    def _handle_website_form(self, model_name, **kwargs):
        model_record = request.env['ir.model'].sudo().search(
            [('model', '=', model_name), ('website_form_access', '=', True)])
        if not model_record:
            return json.dumps({
                'error': _("The form's specified model does not exist")
            })

        if model_name == 'hr.applicant':
            applicant = request.env[model_name].sudo().search([('email_from','=',request.params['email_from'])])
            user = request.env['res.users'].sudo().search(
                [('login', '=', request.params['email_from']), '|', ('active', '=', True), ('active', '=', False)])
            if user and user.active == False:
                user.toggle_active()
                employee = request.env['hr.employee'].sudo().search(
                    [('user_id', '=', user.id), '|', ('active', '=', True),
                     ('active', '=', False)])
                if employee:
                    employee.toggle_active()
            if applicant or user:
                return json.dumps({
                    'error': _('Account already exist. Please go to Sign in and choose for Reset Password')
                })
            else:
                try:
                    data = self.extract_data(model_record, request.params)
                # If we encounter an issue while extracting data
                except ValidationError as e:
                    # I couldn't find a cleaner way to pass data to an exception
                    return json.dumps({'error_fields': e.args[0]})

                try:
                    id_record = self.insert_record(request, model_record, data['record'], data['custom'], data.get('meta'))
                    if id_record:
                        self.insert_attachment(model_record, id_record, data['attachments'])
                        # in case of an email, we want to send it immediately instead of waiting
                        # for the email queue to process
                        if model_name == 'mail.mail':
                            request.env[model_name].sudo().browse(id_record).send()

                # Some fields have additional SQL constraints that we can't check generically
                # Ex: crm.lead.probability which is a float between 0 and 1
                # TODO: How to get the name of the erroneous field ?
                except IntegrityError:
                    return json.dumps(False)

                request.session['form_builder_model_model'] = model_record.model
                request.session['form_builder_model'] = model_record.name
                request.session['form_builder_id'] = id_record

                return json.dumps({'id': id_record})


class WebsiteJob(http.Controller):

    @http.route('''/jobs/apply/generic''', type='http', auth="public", website=True, sitemap=True)
    def jobs_apply_generic(self, **kwargs):
        error = {}
        default = {}
        if 'website_hr_recruitment_error' in request.session:
            error = request.session.pop('website_hr_recruitment_error')
            default = request.session.pop('website_hr_recruitment_default')
        countries = request.env['res.country'].search([])
        return request.render("website_hr_recruitment.apply", {
            'countries': countries,
            'error': error,
            'default': default,
        })

    @http.route('''/jobs/detail/<model("hr.job"):job>''', type='http', auth="public", website=True, sitemap=True)
    def jobs_detail(self, job, **kwargs):
        if not job.can_access_from_current_website():
            raise NotFound()

        return request.render("website_hr_recruitment.detail", {
            'job': job,
            'main_object': job
        })

    @http.route('''/jobs/apply/<model("hr.job"):job>''', type='http', auth="public", website=True, sitemap=True)
    def jobs_apply(self, job, **kwargs):
        user = request.env.user
        if not job.can_access_from_current_website():
            raise NotFound()

        if user.login != 'public':
            emp = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
            applicant = request.env['hr.applicant'].sudo().search([('emp_id', '=', emp.id)], limit=1)
            print(applicant.stage_id)
            if emp and not applicant:
                scenario = 3
            elif applicant:
                scenario = 0
                if applicant.job_id:
                    scenario = 3
                else:
                    if not applicant.stage_id:
                        scenario = 1
                    else:
                        applicant.job_id = job.id
                        scenario = 2
            return request.render("website_hr_recruitment.detail", {
                'job': job,
                'main_object': job,
                'scenario': scenario
            })
        else:
            error = {}
            default = {}
            if 'website_hr_recruitment_error' in request.session:
                error = request.session.pop('website_hr_recruitment_error')
                default = request.session.pop('website_hr_recruitment_default')
            countries = request.env['res.country'].search([])
            return request.render("website_hr_recruitment.apply", {
                'countries':countries,
                'job': job,
                'error': error,
                'default': default,
            })

class WebsiteSkills(http.Controller):
    
    def get_domain_my_line_ids(self, user):
        emp = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)],
                                                limit=1)
        return [
            ('employee_id', '=', emp and emp.id or False),
        ]

    @http.route(['/my/skills'], type='http', auth="user", website=True)
    def my_skills(self, **kwargs):
        Lines_sudo = request.env['hr.resume.line'].sudo()
        Lines_skills_sudo = request.env['hr.employee.skill'].sudo()
        user = request.env.user
        emp = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)],limit=1)
        lines = request.env['hr.resume.line'].search(self.get_domain_my_line_ids(request.env.user))
        skill_lines = request.env['hr.employee.skill'].search(self.get_domain_my_line_ids(request.env.user))
        skill_type = request.env['hr.resume.line.type'].search([])
        
        m_skill_type = request.env['hr.skill.type'].search([])
        skill_ids = request.env['hr.skill'].search([])
        skill_level_ids = request.env['hr.skill.level'].search([])
        grouped_lines = [Lines_sudo.concat(*g) for k, g in groupbyelem(lines, itemgetter('line_type_id'))]
        
        grouped_skills_lines = [Lines_skills_sudo.concat(*g) for k, g in groupbyelem(skill_lines, itemgetter('skill_type_id'))]
        values = {
            'line_ids': lines,
            'grouped_lines':grouped_lines,
            'grouped_skills_lines': grouped_skills_lines,
            'skill_type': skill_type,
            'm_skill_type':m_skill_type,
            'skill_ids': skill_ids,
            'skill_level_ids': skill_level_ids,
            'employee_id':emp
        }
        return request.render("dws_dae_recruitment.skills", values)
    
    @http.route(['''/my/resume_line/<model('hr.resume.line'):skill>'''], type='http', auth="user", website=True)
    def portal_my_resume_line(self, skill, **kw):
        user = request.env.user
        emp = request.env['hr.employee'].search([('user_id', '=', user.id)],
                                                limit=1)
        skill_type = request.env['hr.resume.line.type'].search([])
        return request.render(
            "dws_dae_recruitment.portal_my_resume_line_template", {
                'skill': skill,
                'skill_type': skill_type
            })
        
    @http.route(['''/my/skill_line/<model('hr.employee.skill'):skill>'''], type='http', auth="user", website=True)
    def portal_my_skill_line(self, skill, **kw):
        user = request.env.user
        emp = request.env['hr.employee'].search([('user_id', '=', user.id)],
                                                limit=1)
        hr_skill_type = request.env['hr.skill.type'].search([])
        hr_skill = request.env['hr.skill'].search([])
        hr_skill_level = request.env['hr.skill.level'].search([])
        return request.render(
            "dws_dae_recruitment.portal_my_skill_line_template", {
                'skill': skill,
                'skill_type': hr_skill_type,
                'hr_skill': hr_skill,
                'hr_skill_level': hr_skill_level
            })
