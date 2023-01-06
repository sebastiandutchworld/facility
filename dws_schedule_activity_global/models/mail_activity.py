# -*- coding: utf-8 -*-

from odoo import models, fields, api
import json

class MailActivity(models.Model):
   
    _inherit = 'mail.activity'
    
    supervisor_user_id = fields.Many2one(
        'res.users',
        string='Supervisor',
        copy=False,
    )
    
    link_to_model = fields.Char(string='Document Name', compute='_compute_origin_link')

    @api.depends('res_model')
    def _compute_origin_link(self):
        for activity in self:
            links = []
            if activity.res_model:
                click = 1
                rec = self.env[activity.res_model].search([('id', '=', activity.res_id)])
                if not rec:
                    click = 0
                links.append((activity.res_id, activity.res_model, activity.res_name, click))
                activity.link_to_model = json.dumps(links)
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

    
