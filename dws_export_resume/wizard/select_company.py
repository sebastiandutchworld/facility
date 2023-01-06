from odoo import _, api, fields, models, tools
from odoo.http import request

import logging
_logger = logging.getLogger(__name__)


class SelectCompany(models.TransientModel):
    _name = 'select.company'
    company_id = fields.Many2one('res.company', string='Company', index=True,
                                 default=lambda self: self.default_company_id(),domain="['|',('partner_id.name', '=', 'Daedalus'),('partner_id.name', '=', 'EML')]")

    def default_company_id(self):
        employee_id = self.env.context['employee_id']
        leads = request.env['crm.lead'].sudo().search([('vacancies.employee_ids', 'in', [employee_id])])
        # all ids for all companies where the employee has a lead (unique ids)
        lc_ids = list(set(map(lambda lead: lead.company_id.id, leads)))

        # if the employee has all the leads for a single company return that company id (default selection)
        # else (if the employee doesn't have any leads or has leads in multiple companies) return None (no selection)
        return lc_ids[0] if len(lc_ids) == 1 else None

    def generate_resume_for_selected_company(self):
        employee_id = self.env.context['employee_id']
        target_employee = self.env['hr.employee'].browse(employee_id)
        result = target_employee.generate_resume(self.company_id)
        return result
