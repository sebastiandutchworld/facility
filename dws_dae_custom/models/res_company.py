# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    project_other_hours = fields.Many2one('project.project', "Project 'Other Hours'")
    task_vacation = fields.Many2one('project.task', "Task 'Vacation'")
    task_adv = fields.Many2one('project.task', "Task 'Adv'")
    task_all = fields.Many2one('project.task', "Task 'Above legal'")
    task_illness = fields.Many2one('project.task', "Task 'Illness'")
    task_nw = fields.Many2one('project.task', "Task 'Non Working'")
    outsourcing_company = fields.Boolean("Outsourcing Company")


