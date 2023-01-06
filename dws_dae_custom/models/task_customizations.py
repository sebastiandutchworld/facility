# -*- coding: utf-8 -*-

import logging
from odoo import api, models, fields
from datetime import date, timedelta
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning

class TaskCustomizations(models.Model):
    _inherit="project.task"

    email = fields.Char('Email')
    phone = fields.Char('Phone')
    commuter_kilometers = fields.Char('Home-Work Kilometers')
    overtime = fields.Boolean(compute='_overtime')
    activity_created = fields.Boolean(default=False)
    customer_contact = fields.Many2one('res.partner', string='Customer Approver')
    customer_contact2 = fields.Many2one('res.partner', string='Second Customer Approver')
    customer = fields.Char(compute='_customer', store=True)
    contact_list = fields.Many2many('res.partner',compute='_get_contacts')

    def _get_contacts(self):
        for obj in self:
            contact_ids = []
            users = self.env['res.users'].search([])

            for user in users:
                if not user.has_group('base.group_portal'):
                    contact_ids.append(user.partner_id.id)
            obj.contact_list = [(6, 0, contact_ids)]

    @api.depends('project_id')
    def _customer(self):
        for rec in self:
            if rec.project_id.partner_id.name:
                rec.customer = rec.project_id.partner_id.name
            else:
                rec.customer = False

    @api.constrains('customer_contact2')
    def _raise_email_error(self):
        if self.customer_contact2.email == self.customer_contact.email and self.customer_contact:
            raise ValidationError('Email of second approver may not be the same as for the first approver')

    # original onchange action defined in project.task overwritten here by customer request. The idea is to keep the start date when the assigned user is changed

    @api.onchange('user_id')
    def _onchange_user(self):
        if self.user_id:
            self.planned_date_begin = self.planned_date_begin

    def update_date_end(self, stage_id):
        return {'date_end': self.date_end}


    def _overtime(self):
        for rec in self:
            if rec.project_id.sale_order_id:
                if rec.project_id.sale_order_id[0].overtime:
                    rec.overtime = rec.project_id.sale_order_id[0].overtime
                else:
                    rec.overtime = False
            else:
                    rec.overtime = False

    def _cron_task_end_date(self):
        days = -1
        for project in self.env['project.project'].search([]):
            if project.sale_order:
                tasks = self.read_group([('project_id', '=', project.id), ('stage_id', '!=', 10)], ['user_ids'], ['user_ids'])
                assigned_users = [task['user_ids'][0] for task in tasks if task['user_ids']]
                if len(assigned_users) > 0:
                    for user_id in assigned_users:
                        # second order by id neccessary to obtain the same task every time the cron job is run
                        task_latest_end_date = self.search([('project_id', '=', project.id), ('user_ids', '=', user_id), ('stage_id', '!=', 10)],
                                                           order='planned_date_end desc, id', limit=1)
                        today = date.today()
                        if task_latest_end_date.planned_date_end:
                            end_date = fields.Datetime.from_string(task_latest_end_date.planned_date_end).date()
                            days = (end_date - today).days
                        if 0 <= days <= 180:
                            if not task_latest_end_date.activity_created:
                                name = 'Einddatum: ' + project.name
                                description = "Het project '" + project.name + "' heeft geen taken met een einddatum verder dan: " + end_date.strftime('%Y-%m-%d')
                                activity_type_id = self.env['mail.activity.type'].with_context(lang='en_US').search([('name', '=', 'Todo')], limit=1)
                                self.env['mail.activity'].create({
                                    'res_id': task_latest_end_date.id,
                                    'res_model_id': self.env['ir.model']._get('project.task').id,
                                    'activity_type_id': activity_type_id.id,
                                    'summary': "Het project '" + project.name + "' heeft geen taken met een einddatum verder dan: " + end_date.strftime('%Y-%m-%d'),
                                    'user_id': 110, # Ingrid
                                    'date_deadline': today
                                })
                                task_latest_end_date.activity_created = True

    def _message_auto_subscribe_followers(self, updated_values, default_subtype_ids):
        """ Optional method to override in addons inheriting from mail.thread.
        Return a list tuples containing (
          partner ID,
          subtype IDs (or False if model-based default subtypes),
          QWeb template XML ID for notification (or False is no specific
            notification is required),
          ), aka partners and their subtype and possible notification to send
        using the auto subscription mechanism linked to updated values.

        Default value of this method is to return the new responsible of
        documents. This is done using relational fields linking to res.users
        with track_visibility set. Since OpenERP v7 it is considered as being
        responsible for the document and therefore standard behavior is to
        subscribe the user and send him a notification.

        Override this method to change that behavior and/or to add people to
        notify, using possible custom notification.

        :param updated_values: see ``_message_auto_subscribe``
        :param default_subtype_ids: coming from ``_get_auto_subscription_subtypes``
        """
        print('auto subscription is triggered')
        fnames = []
        field = self._fields.get('user_id')
        user_id = updated_values.get('user_id')
        if field and user_id and field.comodel_name == 'res.users' and (
                getattr(field, 'track_visibility', False) or getattr(field, 'tracking', False)):
            user = self.env['res.users'].sudo().browse(user_id)
            # # if not internal user, then do not message auto subscribe follower
            # if user.share:
            #     return []
            try:  # avoid to make an exists, lets be optimistic and try to read it.
                if user.active:
                    # set template false if not internal user
                    return [(user.partner_id.id, default_subtype_ids,
                             'mail.message_user_assigned' if (
                                         user != self.env.user and user.share == False) else False)]
            except:
                pass
        return []

class ProjectCustomizations(models.Model):
    _inherit = "project.project"

    sale_order = fields.Many2one('sale.order', 'Sale Order', compute='_sale_order_name')
    project_invoicing = fields.Boolean("Project Invoicing")

    def _sale_order_name(self):
        for rec in self:
            sale_order = rec.env['sale.order'].search([('analytic_account_id', '=', rec.analytic_account_id.id)])
            rec.sale_order = sale_order

    @api.model
    def create(self, vals):
        res = super(ProjectCustomizations, self.sudo()).create(vals)
        #set the right project invoicing value based on the setting at company level
        if res.company_id.outsourcing_company == True:
            project_invoicing = False
        else:
            project_invoicing = True

        res.project_invoicing = project_invoicing

        return res
