# -*- coding: utf-8 -*-

import json
import re
import uuid
from functools import partial

from lxml import etree
from dateutil.relativedelta import relativedelta
from werkzeug.urls import url_encode

from odoo import api, exceptions, fields, models, _
from odoo.tools import float_is_zero, float_compare, pycompat
from odoo.tools.misc import formatLang

from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning

from odoo.tools.safe_eval import safe_eval

from odoo.addons import decimal_precision as dp
from itertools import groupby
import logging

_logger = logging.getLogger(__name__)

class SaleCustomizations(models.Model):
    _inherit = "sale.order"

    tags = fields.Many2many('sale.order.tags', string='Tags')
    overtime = fields.Boolean(compute='_overtime')
    threshold_reached = fields.Boolean(default=False)
    contract_name = fields.Char('Contract Name')
    export_license = fields.Char('Export License')
    export_license_number = fields.Char(compute="_get_export_license", store="True")

    @api.depends("export_license")
    def _get_export_license(self):
        for record in self:
            if record.export_license:
                record.export_license_number = "NL0074CDIU %s" % record.export_license
            else:
                record.export_license_number = ""

    def _prepare_analytic_account_data(self, prefix=None):
        """
        Prepare method for analytic account data
        :param prefix: The prefix of the to-be-created analytic account name
        :type prefix: string
        :return: dictionary of value for new analytic account creation
        """
        name = self.contract_name
        if prefix:
            name = prefix + ": " + name
        return {
            'name': name,
            'code': self.client_order_ref,
            'company_id': self.company_id.id,
            'partner_id': self.partner_id.id
        }    

    def action_sheet_invoice_create(self, grouped=False, final=False, sheet=False, tasks=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']

        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # 1) Create invoices.
        invoice_vals_list = []
        for order in self:
            pending_section = None

            # Invoice values.
            invoice_vals = order._prepare_invoice()

            # Invoice line values (keep only necessary sections).
            for line in order.order_line:
                if line.task_id.id in tasks and not line.task_id.project_id.project_invoicing:
                    print("task is there")
                    approvals = self.env['employee_sheet.approvals'].search(
                        [('sheet_id', '=', sheet.id), ('project_id', '=', line.task_id.project_id.id),
                         ('pdf_report', '!=', False)])
                    if approvals:
                        print("approval is there")
                        invoice_vals['employee_sheet_id'] = sheet.id
                        invoice_vals['approval_id'] = approvals[0].id


                        hours = self.env['account.analytic.line'].search(
                            [('task_id', '=', line.task_id.id), ('date', "<=", sheet.enddate),
                             ('date', ">=", sheet.startdate)])
                        line.qty_to_invoice = 0
                        for hour in hours:
                            line.qty_to_invoice += hour.unit_amount

                        if line.display_type == 'line_section':
                            pending_section = line
                            continue
                        if line.display_type != 'line_note' and float_is_zero(line.qty_to_invoice, precision_digits=precision):
                            continue
                        print("qty to invoice:" + str(line.qty_to_invoice))
                        if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final) or line.display_type == 'line_note':
                            if pending_section:
                                invoice_vals['invoice_line_ids'].append((0, 0, pending_section._prepare_invoice_line()))
                                pending_section = None
                            invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_invoice_line()))

            if not invoice_vals['invoice_line_ids']:
                raise UserError(_(
                    'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(_(
                'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

        # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
        if not grouped:
            new_invoice_vals_list = []
            invoice_grouping_keys = self._get_invoice_grouping_keys()
            for grouping_keys, invoices in groupby(invoice_vals_list,
                                                   key=lambda x: [x.get(grouping_key) for grouping_key in
                                                                  invoice_grouping_keys]):
                origins = set()
                payment_refs = set()
                refs = set()
                ref_invoice_vals = None
                for invoice_vals in invoices:
                    if not ref_invoice_vals:
                        ref_invoice_vals = invoice_vals
                    else:
                        ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                    origins.add(invoice_vals['invoice_origin'])
                    payment_refs.add(invoice_vals['payment_reference'])
                    refs.add(invoice_vals['ref'])
                ref_invoice_vals.update({
                    'ref': ', '.join(refs)[:2000],
                    'invoice_origin': ', '.join(origins),
                    'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
                })
                new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.

        # As part of the invoice creation, we make sure the sequence of multiple SO do not interfere
        # in a single invoice. Example:
        # SO 1:
        # - Section A (sequence: 10)
        # - Product A (sequence: 11)
        # SO 2:
        # - Section B (sequence: 10)
        # - Product B (sequence: 11)
        #
        # If SO 1 & 2 are grouped in the same invoice, the result will be:
        # - Section A (sequence: 10)
        # - Section B (sequence: 10)
        # - Product A (sequence: 11)
        # - Product B (sequence: 11)
        #
        # Resequencing should be safe, however we resequence only if there are less invoices than
        # orders, meaning a grouping might have been done. This could also mean that only a part
        # of the selected SO are invoiceable, but resequencing in this case shouldn't be an issue.
        if len(invoice_vals_list) < len(self):
            SaleOrderLine = self.env['sale.order.line']
            for invoice in invoice_vals_list:
                sequence = 1
                for line in invoice['invoice_line_ids']:
                    line[2]['sequence'] = SaleOrderLine._get_invoice_line_sequence(new=sequence,
                                                                                   old=line[2]['sequence'])
                    sequence += 1

        # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
        # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
        moves = self.env['account.move'].sudo().with_context(default_type='out_invoice').create(invoice_vals_list)
        self.env['ir.attachment'].create({
            # 'name': 'Signed approval',
            'name': '%s_%s_%s_approved.pdf' % (
                approvals[0].project_id.name, approvals[0].sheet_id.startdate,
                approvals[0].sheet_id.user_id.name.replace(" ", "_")),
            'type': 'binary',
            'datas': approvals[0].pdf_report,
            'res_model': 'account.move',
            'res_id': moves[0].id,
            'mimetype': 'application/pdf'
        })

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
        for move in moves:
            move.message_post_with_view('mail.message_origin_link',
                                        values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
                                        subtype_id=self.env.ref('mail.mt_note').id
                                        )
        return moves

    @api.depends('tags')
    def _overtime(self):
        for so in self:
            ot = False
            if so.tags:
                for tag in so.tags:
                    if tag.name.lower() == 'overtime':
                        ot = True
                        #so.overtime = True
                        break
            so.overtime = ot

    def action_view_task(self):
        self.ensure_one()

        list_view_id = self.env.ref('project.view_task_tree2').id
        form_view_id = self.env.ref('project.view_task_form2').id

        action = {'type': 'ir.actions.act_window_close'}
        task_projects = self.tasks_ids.mapped('project_id')
        if len(task_projects) == 1 and len(
                self.tasks_ids) > 1:  # redirect to task of the project (with kanban stage, ...)
            action = self.with_context(active_id=task_projects.id).env['ir.actions.actions']._for_xml_id(
                'project.act_project_project_2_project_task_all')
            action['domain'] = [('id', 'in', self.tasks_ids.ids)]
            # set order of views
            action['views'] = [[False, 'tree'], [False, 'kanban'], [False, 'form'],
                                        [False, 'calendar'], [False, 'pivot'], [False, 'graph'], [False, 'activity']]
            if action.get('context'):
                eval_context = self.env['ir.actions.actions']._get_eval_context()
                eval_context.update({'active_id': task_projects.id})
                action_context = safe_eval(action['context'], eval_context)
                action_context.update(eval_context)
                action['context'] = action_context
        else:
            action = self.env["ir.actions.actions"]._for_xml_id("project.action_view_task")
            action['context'] = {}  # erase default context to avoid default filter
            if len(self.tasks_ids) > 1:  # cross project kanban task
                action['views'] = [[list_view_id, 'tree'], [False, 'kanban'], [form_view_id, 'form'], [False, 'graph'],
                                   [False, 'calendar'], [False, 'pivot']]
            elif len(self.tasks_ids) == 1:  # single task -> form view
                action['views'] = [(form_view_id, 'form')]
                action['res_id'] = self.tasks_ids.id
        # filter on the task of the current SO
        action.setdefault('context', {})
        action['context'].update({'search_default_sale_order_id': self.id})
        return action

class SaleOrderTags(models.Model):
    _name = "sale.order.tags"
    _description = "Tags of Sale Order"

    name = fields.Char(required=True)
    color = fields.Integer(string='Color Index', default=10)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]

class InvoiceCustomizations(models.Model):
    _inherit="account.move"

    sale_order = fields.Many2one('sale.order', compute='_sale_order')

    from_email = fields.Char(compute='_get_from_email')

    overwork_rates = fields.Text(string='Overwork Rates', compute='_overwork_rates')
    contract_name = fields.Char(compute='_contract_name')
    overtime = fields.Boolean(string='Overtime', compute='_overtime', readonly=True, store=True)
    #overtime = fields.Boolean(string='Overtime', readonly=True, store=True)
    signed_pdf_name = fields.Char(compute='_signed_pdf_name')
    #payment_term_exact_code = fields.Char(related='payment_term_id.exact_code')

    def _get_from_email(self):
        for invoice in self:
            company_name = invoice.company_id.name
            #print('name: ', company_name)
            if company_name == 'Daedalus':
                invoice.from_email = 'facturen@daedalus.nl'
            elif company_name == 'EML':
                invoice.from_email = 'facturen@eml.nl'
            else:
                invoice.from_email = 'finance@gearboks.nl'

    @api.depends('invoice_origin')
    def _sale_order(self):
        for invoice in self:
            invoice.sale_order = self.env['sale.order'].search([('name', '=', invoice.invoice_origin)], limit=1)


    @api.depends('sale_order')
    def _overwork_rates(self):
        for invoice in self:
            if invoice.sale_order:
                invoice.overwork_rates = invoice.sale_order.overwork_rates
            else:
                invoice.overwork_rates = ''

    @api.depends('sale_order')
    def _contract_name(self):
        for invoice in self:
            if invoice.sale_order:
                invoice.contract_name = invoice.sale_order.contract_name
            else:
                invoice.contract_name = ''

    @api.depends('sale_order')
    def _overtime(self):
        for invoice in self:
            if invoice.sale_order.overtime:
                invoice.overtime = invoice.sale_order.overtime
            else:
                invoice.overtime = False

    @api.depends('approval_id')
    def _signed_pdf_name(self):
        for invoice in self:
            if invoice.approval_id:
                approval = self.env['employee_sheet.approvals'].browse(invoice.approval_id.id)
                invoice.signed_pdf_name = '%s_%s_%s_approved.pdf;' % (
                                    approval.project_id.name, approval.sheet_id.startdate, approval.sheet_id.user_id.name.replace(" ", "_"))
            else:
                invoice.signed_pdf_name = ''
                
class CustomSaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _timesheet_create_project_prepare_values(self):
        """Generate project values"""
        account = self.order_id.analytic_account_id
        if not account:
            self.order_id._create_analytic_account(prefix=self.product_id.default_code or None)
            account = self.order_id.analytic_account_id

        # create the project or duplicate one
        return {
            'name': '%s (%s)' % (self.order_id.contract_name,
                                        self.order_partner_id.ref) if self.order_partner_id.ref else self.order_id.contract_name,
            'analytic_account_id': account.id,
            'partner_id': self.order_id.partner_id.id,
            'sale_line_id': self.id,
            'sale_order_id': self.order_id.id,
            'active': True,
            'company_id': self.company_id.id,
            'allow_billable': True
        }    

    def _timesheet_create_task_prepare_values(self, project):
        self.ensure_one()
        planned_hours = self._convert_qty_company_hours(self.company_id)
        sale_line_name_parts = self.name.split('\n')
        title = sale_line_name_parts[0] or self.product_id.name
        description = '<br/>'.join(sale_line_name_parts[1:])
        return {
            'name': '%s:%s' % (self.order_id.contract_name or '', self.name.split('\n')[0] or self.product_id.name),
            'planned_hours': planned_hours,
            'partner_id': self.order_id.partner_id.id,
            'email_from': self.order_id.partner_id.email,
            'description': description,
            'project_id': project.id,
            'sale_line_id': self.id,
            'sale_order_id': self.order_id.id,
            'company_id': project.company_id.id,
            'user_ids': False,  # force non assigned task, as created as sudo()
        }