# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
from dateutil.relativedelta import relativedelta, MO,SU
from odoo.exceptions import UserError, AccessError


class EployeeSheetInvoiceWizard(models.TransientModel):
    _name = 'employee.sheet.invoice.wizard'


    def get_related_saleorders(self,sheet):
        self.env.cr.execute('SELECT DISTINCT task_id FROM employee_hours WHERE task_id is not NULL AND (regular > 0 OR overtime > 0 OR vacation > 0 OR adv > 0 OR illness > 0 OR nw > 0) AND employee_sheet_id = ' + str(sheet.id))
        task_ids = [x[0] for x in self.env.cr.fetchall()]
        #hours = self.env['employee.hours'].browse(hour_ids)
        sale_orders = []
        for task_id in task_ids:
            sale_order_line = self.env['sale.order.line'].search([('task_id','=',task_id)])
            if sale_order_line and sale_order_line[0].order_id not in sale_orders:
                sale_orders.append(sale_order_line[0].order_id)
        return sale_orders

    def get_related_tasks(self, sheet):
        self.env.cr.execute(
            'SELECT DISTINCT task_id FROM employee_hours WHERE task_id is not NULL AND employee_sheet_id = ' + str(
                sheet.id))
        hour_ids = [task_id[0] for task_id in self.env.cr.fetchall()]
        return hour_ids

    def invoice_timesheets(self):
        for sheet in self.env['employee.sheet'].browse(self._context.get('active_ids', [])):
            #sheet = self.env['employee.sheet'].browse(activeid)
            if int(sheet.status) == 4:
                sale_orders = self.get_related_saleorders(sheet)
                print(sale_orders)
                tasks = self.get_related_tasks(sheet)
                invoiceability = False
                for sale_order in sale_orders:
                    invoice = sale_order.action_sheet_invoice_create(False, False, sheet, tasks)
                    if invoice is not False:
                        invoice._link_timesheets_to_invoice(None, None)
                        invoiceability = True
                if invoiceability == False:
                    raise UserError(_('There is no invoicable line for: ' + str(sheet.employee.name)))
                sheet.write({'status': '5'})

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: