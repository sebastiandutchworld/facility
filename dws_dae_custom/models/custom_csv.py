# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

import datetime,csv
from odoo import api, fields, models, _

class CustomCSV(models.TransientModel):
    _name = 'csv.custom_csv'

    moves = fields.Char()

    def _get_records(self, model):
        if self.env.context.get('active_domain'):
            records = model.search(self.env.context.get('active_domain'))
        elif self.env.context.get('active_ids'):
            records = model.browse(self.env.context.get('active_ids', []))
        else:
            records = model.browse(self.env.context.get('active_id', []))
        d = []
        for item in records:
            d.append(str(item.id))
        return records

    @api.model
    def default_get(self, fields):
        result = super(CustomCSV, self).default_get(fields)

        active_model = self.env.context.get('active_model')
        model = self.env[active_model]

        records = self._get_records(model)
        d = []
        for item in records:
            d.append(str(item.id))
        return result

    def generate_csv(self):
        csv = ""
        moves = self.moves.split(',')
        journal_entries = self.env['account.move'].browse(list(map(int, moves)))
        for journal_entry in journal_entries:
            values = []
            name = journal_entry.name
            date = journal_entry.date
            date_formatted = fields.Date.from_string(date).strftime("%d%m%Y")
            period = fields.Date.from_string(date).strftime("%m")
            year = fields.Date.from_string(date).strftime("%Y")
            deb_code = journal_entry.partner_id.exact_customer_account_receivable
            boekstuknummer = journal_entry.exact_boekstuknummer
            amount = str(journal_entry.amount)
            invoice_payment_term = self.env['account.payment.term.line'].search(
                [('value', '=', 'balance'), ('payment_id', '=', journal_entry.invoice_payment_term_id.id)])
            invoice_expiration_date = (
            fields.Date.from_string(date) + datetime.timedelta(days=(invoice_payment_term.days))).strftime("%d%m%Y")

            values.append("0")
            values.append("V")
            values.append("4")
            values.append(period.lstrip("0"))
            values.append(year)
            values.append(boekstuknummer)
            values.append(name)
            values.append(date_formatted)
            for i in range(1):
                values.append("")
            values.append(deb_code or "")
            for i in range(2):
                values.append("")
            values.append(amount.replace(".", ","))
            for i in range(5):
                values.append("")
            values.append(invoice_expiration_date)
            for i in range(21):
                values.append("")
            journal_entry_line = ";".join(values)
            csv_row = u'";"'.join(values)
            csv += '"' + csv_row + '"\n'
            index = 0

            for journal_item in journal_entry.line_ids:
                tax = 0.0
                if journal_item.tax_ids:
                    tax = journal_item.tax_ids[0].amount
                values2 = []
                date = journal_item.move_id.date
                date_formatted = fields.Date.from_string(date).strftime("%d%m%Y")
                period = fields.Date.from_string(date).strftime("%m")
                year = fields.Date.from_string(date).strftime("%Y")
                account = journal_item.account_id.code
                name = journal_item.move_id.name
                credit = str(journal_item.credit)
                if (journal_item.credit == 0) or (account == "150000"):
                    continue
                btw_code = (journal_item.tax_ids.exact_btw_code or '')
                rel_code = (journal_item.partner_id.exact_customer_account_receivable or '')
                index += 1

                values2.append(str(index))
                values2.append("V")
                values2.append("4")
                values2.append(period.lstrip("0"))
                values2.append(year)
                for i in range(1):
                    values2.append("")
                values2.append(name)
                values2.append(date_formatted)
                values2.append(account)
                values2.append(rel_code)
                for i in range(2):
                    values2.append("")
                values2.append((str(round((journal_item.credit * (1 + (tax / 100))),2))).replace(".", ","))
                for i in range(7):
                    values2.append("")
                values2.append(btw_code)
                for i in range(19):
                    values2.append("")
                journal_item_line = ";".join(values2)
                csv_row2 = u'";"'.join(values2)
                csv += '"' + csv_row2 + '"\n'
                print('journal_item: ', journal_item_line)
        return csv

    def action_generate_csv(self):
        print("test")
        active_model = self.env.context.get('active_model')
        model = self.env[active_model]
        records = self._get_records(model)
        d = []
        for item in records:
            d.append(str(item.id))

        self.moves = str(",".join(d))

        return {
            'type': 'ir.actions.act_url',
            #'url': "/csv/download/" + str(",".join(d)),
            'url': "/csv/download/" + str(self.id),
            'target': 'self',
        }