from odoo import api, fields, models, _

class HrVacancy(models.Model):
    _name = "hr.vacancy"

    name = fields.Char(string="Name",compute='_compute_name')
    job_id = fields.Many2one('hr.job', "Job")
    qty = fields.Integer("Quantity")
    lead_id = fields.Many2one('crm.lead', "Lead")
    employee_ids = fields.Many2many('hr.employee', 'hr_employee_hr_vacancy_rel', 'vacancy_id', 'employee_id', string='Candidates')

    def _compute_name(self):
        for rec in self:
            rec.name = rec.job_id.name
        



