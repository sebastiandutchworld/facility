from odoo import api, fields, models

class HrJobInherit(models.Model):

    _inherit = 'hr.job'

    vacancies = fields.One2many('hr.vacancy', 'job_id', string="Vacancies")
