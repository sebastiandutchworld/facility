# -*- coding: utf-8 -*-

from odoo import api, fields, models


class HRRecruitmentStageInherit(models.Model):
    _inherit = "hr.recruitment.stage"

    defines_candidate = fields.Boolean("Candidate definition", default=False)

