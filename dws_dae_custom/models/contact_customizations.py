# -*- coding: utf-8 -*-
import logging
from odoo import api, models, fields

class ContactCustomizations(models.Model):
    _inherit="res.partner"
    _sql_constraints = [(
        'check_name',
        "CHECK( 1=1 )",
        'Contacts require a name.'
    )]

    name = fields.Char(compute='_compute_name', store=True, readonly=False, required=False)
    first_name = fields.Char('First Name')
    initials = fields.Char('Initials')
    surname_prefix = fields.Char('Surname Prefix', required=False)
    surname = fields.Char('Surname')
    maiden_name = fields.Char('Maiden Name')
    maiden_name_prefix = fields.Char('Maiden Name Prefix')
    type = fields.Selection(selection_add=[('foreign', 'Foreign Address'), ('emergency_contact', 'Emergency Contact')])
    company_name2 = fields.Char()
    signature = fields.Binary('Signature', readonly=True)

    @api.depends('first_name', 'surname_prefix', 'surname', 'company_type', 'company_name2')
    def _compute_name(self):
        for rec in self:
            print(rec.is_company)
            if rec.is_company:
                rec.name = rec.company_name2
            elif rec.type == 'foreign':
                rec.name = rec.parent_id.name
            else:
                rec.name = rec._get_computed_name(rec.first_name, rec.surname_prefix, rec.surname)

    def _get_computed_name(self, first_name, prefix, surname):
        return " ".join((p for p in (first_name, prefix, surname) if p))

    @api.onchange("name")
    def _computed_name_company(self):
        for rec in self:
            if rec.is_company:
                rec.company_name2 = rec.name

    def name_get(self):
        res = []
        for partner in self:
            name = partner.name or ''
            # in ['invoice', 'delivery', 'other', 'private', 'foreign', 'emergency_contact']
            if partner.company_name or partner.parent_id:
                if not partner.type == 'contact' and partner.type:
                    name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
                if not partner.is_company:
                    name = "%s, %s" % (partner.commercial_company_name or partner.parent_id.name, name)
            if self._context.get('show_address_only'):
                name = partner._display_address(without_company=True)
            if self._context.get('show_address'):
                name = name + "\n" + partner._display_address(without_company=True)
            if self._context.get('show_emergency'):
                print("test here emergency contact")
                name = (str(partner.name) or '') + "\n" + str(partner.phone or '') + "\n" + str(partner.mobile or '')
            name = name.replace('\n\n', '\n')
            name = name.replace('\n\n', '\n')
            if self._context.get('show_email') and partner.email:
                name = "%s <%s>" % (name, partner.email)
            if self._context.get('html_format'):
                name = name.replace('\n', '<br/>')
            res.append((partner.id, name))
        return res

class ResUser(models.Model):
    _inherit="res.users"

    @api.onchange("first_name", "surname_prefix", "surname")
    def _compute_name(self):
        for record in self:
            record.name = record.partner_id._get_computed_name(record.first_name, record.surname_prefix, record.surname)