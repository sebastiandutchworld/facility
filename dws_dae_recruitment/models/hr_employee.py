from odoo import api, fields, models

class Candidate(models.Model):

    _inherit = 'hr.employee'

    is_applicant = fields.Boolean("Is Applicant", compute = '_compute_is_applicant')
    latest_task_enddate = fields.Date('End date latest task', compute = '_compute_task')
    latest_task = fields.Many2one('project.task', string="Task",compute='_compute_task')
    contract_job_id = fields.Many2one('hr.job', string="Function",compute='_compute_function', store=True)
    application_status = fields.Char(string="Status applicant",compute='_compute_status_applicant', store=True)
    lead_id = fields.Many2many('crm.lead', string="Crm Lead",compute='_compute_lead')#, store=True)
    is_candidate = fields.Boolean("Is Candidate", compute='_compute_is_candidate', store=True)
    vacancy_id = fields.Many2many('hr.vacancy', string="Vacancy", compute='_compute_vacancy')

    def open_applicant(self):
        print(self.applicant_id)
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.applicant',
            'res_id': self.applicant_id[0].id,
            'views': [(False, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {},
        }

    def _compute_is_applicant(self):
        for employee in self:
            if employee.applicant_id.stage_id != False:
                employee.is_applicant = True
            else:
                employee.is_applicant = False

    @api.depends('applicant_id.stage_id','first_contract_date')
    def _compute_is_candidate(self):
        for employee in self:
            employee.is_candidate = False
            if employee.applicant_id.stage_id.defines_candidate != False or employee.first_contract_date:
                employee.is_candidate = True
            else:
                employee.is_candidate = False

    def _compute_task(self):
        for employee in self:
            task = self.env['project.task'].search([('user_ids', 'in', [employee.user_id.id]),('planned_date_end','!=',False)],order='planned_date_end desc',limit=1)
            employee.latest_task_enddate = task.planned_date_end or False
            employee.latest_task = task or False
    def _compute_function(self):
        for employee in self:
            contract = self.env['hr.contract'].search([('employee_id', '=', employee.id),('state','=','open')],limit=1)
            employee.contract_job_id = contract.job_id or False
    @api.depends('applicant_id.stage_id')
    def _compute_status_applicant(self):
        for employee in self:
            employee.application_status = employee.applicant_id.stage_id.name or False

    def _compute_lead(self):
        for employee in self:
            vacancy = self.env['hr.vacancy'].search([('employee_ids', 'in', [employee.id])])
            employee.lead_id = vacancy.lead_id or False
            
    def _compute_vacancy(self):
        for employee in self:
            vacancies = self.env['hr.vacancy'].search([('employee_ids', 'in', [employee.id])])
            employee.vacancy_id = vacancies or False 

    @api.model_create_multi
    def create(self, vals_list):
        res = super(Candidate, self).create(vals_list)
        for employee in res:
            resume_line = self.env['hr.resume.line'].search([('employee_id', '=', employee.id)], limit=1)
            resume_line.unlink()

        return res
