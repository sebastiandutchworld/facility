from odoo import api, fields, models

class Applicant(models.Model):

    _inherit = 'hr.applicant'

    zipcode = fields.Char("Zipcode")
    country_id = fields.Many2one('res.country', string='Country')
    firstname = fields.Char("First name")
    surname_prefix = fields.Char("Surname prefix")
    surname = fields.Char("Surname")
    street = fields.Char("Street")
    surname = fields.Char("Surname")
    housenumber = fields.Char("Housenumber")
    street2 = fields.Char("Street2")
    city = fields.Char("City")
    state = fields.Char("State")
    birthday = fields.Date("Birthday")
    nationality = fields.Many2one('res.country', string='Nationality')
    cv_remainder_7_sent = fields.Boolean("CV Remainder 7 sent")
    cv_remainder_14_sent = fields.Boolean("CV Remainder 14 sent")
    cv_remainder_21_sent = fields.Boolean("CV Remainder 21 sent")

    def action_view_employee(self):
        self.ensure_one()
        action_window = {
            "type": "ir.actions.act_window",
            "res_model": "hr.employee",
            "name": "Employee",
            "views": [[False, "form"]],
            "res_id": self.emp_id.id
        }

        return action_window

    @api.model
    def create(self, vals):
        if 'partner_name' not in vals:
            vals['partner_name'] = "applicant"
        if 'name' not in vals:
            vals['name'] = "applicant"
        if 'surname_prefix' not in vals:
            vals['surname_prefix'] = ''
        if 'surname' in vals and 'firstname' in vals:
            vals['name'] = vals['partner_name'] = str(vals['firstname']) + ' ' + str(vals['surname_prefix']) + ' ' + str(vals['surname'])
        
        if 'stage_id' in vals:
            vals['stage_id'] = False
        applicant = super(Applicant, self).create(vals)
        #applicant.stage_id = False

        contact_name = False

        if not applicant.partner_name:
            raise UserError(_('You must define a Contact Name for this applicant.'))
        new_partner_id = self.env['res.partner'].create({
            'is_company': False,
            'type': 'private',
            'name': applicant.name,
            'email': applicant.email_from,
            'phone': applicant.partner_phone,
            'mobile': applicant.partner_mobile,
            'surname': applicant.surname,
            'surname_prefix': applicant.surname_prefix or '',
            'first_name': applicant.firstname,
            'street_name': applicant.street,
            'street2': applicant.street2 or '',
            'city': applicant.city,
            'street_number': applicant.housenumber,
            'zip': applicant.zipcode,
            'country_id': applicant.country_id.id,
            'company_id': applicant.job_id.company_id.id or 1
        })
        applicant.partner_id = new_partner_id
        if applicant.partner_name or contact_name:
            employee_data = {
                'name': applicant.partner_name or contact_name,
                'job_id': applicant.job_id.id,
                'job_title': applicant.job_id.name,
                'department_id': applicant.department_id.id or False,
                'address_id': applicant.company_id and applicant.company_id.partner_id
                                      and applicant.company_id.partner_id.id or False,
                'work_email': applicant.email_from,
                'work_phone': applicant.partner_phone,
                'applicant_id': applicant.ids,
                'birthday': applicant.birthday,
                'country_id': applicant.nationality.id
            }

        print(employee_data)
        employee = self.env['hr.employee'].create(employee_data)
        x_group_portal_user = self.env.ref('base.group_portal')
        user = self.env['res.users'].sudo().create([{'name': employee.name,
                                  'login': new_partner_id.email,
                                  'partner_id': new_partner_id.id,
                                  'company_id': applicant.job_id.company_id.id or 1, #force Daedalus company for now but it needs to be discussed!!
                                  'groups_id': [(6, 0, [x_group_portal_user.id])],
                                  }])
        employee.write({'user_id':user.id})
        #print(employee.user_id)
        #employee.with_context(active_id=employee.id).send_invitation_email()

        return applicant