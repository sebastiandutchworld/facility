# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ApplicantGetRefuseReasonInherit(models.TransientModel):
    _description = 'Get Refuse Reason'
    _inherit = "applicant.get.refuse.reason"


    def action_refuse_reason_apply(self):
        for applicant in self.applicant_ids:
            partner = self.env['res.partner'].browse(applicant.partner_id.id)
            employee = self.env['hr.employee'].search([('applicant_id','=',applicant.id)])
            if employee:
                employee.action_archive()
            if partner:
                user = self.env['res.users'].search([('partner_id', '=', partner.id)])
                if user:
                    print(user)
                    user._write({'active': False})
                    partner._write({'active': False})
                    # user.action_archive()
                    # user.partner_id.action_archive()
                    # if user.active:
                    #     user.write({'active': False})
                    #     user.partner_id.write({'user_ids': [(3, user.id)]})
                    #     self.env.cr.commit()
                    #     user.partner_id.toggle_active()
                    # partner.action_archive()
                    # user.write({'partner_id': False})
                    # partner.write({'user_ids': False})
                    # user.write({'active': False})
                    # partner.write({'active': False})


        return self.applicant_ids.write({'refuse_reason_id': self.refuse_reason_id.id, 'active': False})