from odoo import api, fields, models

class CrmLeadInherit(models.Model):

    _inherit = 'crm.lead'

    vacancies = fields.One2many('hr.vacancy', 'lead_id', string="Vacancies")
