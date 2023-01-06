# See LICENSE file for full copyright and licensing details.

import random
from odoo import api, fields, models, _
from datetime import datetime, time
from odoo.tools import float_compare
from odoo.tools.float_utils import float_round
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class EmpPortalSkill(models.Model):
    _inherit = "hr.employee.skill"
    
    @api.model
    def create_skill_line(self, values):
        if not (self.env.user.employee_id):
            raise AccessDenied()
        user = self.env.user
        self = self.sudo()
        if not (values['skill_type_id'] and values['skill_id'] and values['skill_level_id']):
            return {
                'errors': _('All fields are required !')
            }
        values = {
            'skill_type_id': int(values['skill_type_id']),
            'skill_id': int(values['skill_id']),
            'skill_level_id': int(values['skill_level_id']),
            'employee_id': values['employee_id'],
        }
        myline = self.env['hr.employee.skill'].sudo().create(values)
        return {
            'id': myline.id
        }

    def update_skill_portal(self, values):
        for skill in self:
            skill_values = {
                'skill_type_id': int(values['skill_type_id']),
                'skill_id': int(values['skill_id']),
                'skill_level_id': int(values['skill_level_id']),
            }
            if values['skillID']:
                skill_rec = self.env['hr.employee.skill'].sudo().browse(values['skillID'])
                if skill_rec:
                    skill_rec.sudo().write(skill_values)
