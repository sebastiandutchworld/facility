from odoo import api, fields, models, _

class ResourceCalendar(models.Model):
    _name = "resource.calendar"
    _inherit = ['resource.calendar']

    contract_hours = fields.Float(compute='_contract_hours',string='Contract hours')

    def _contract_hours(self):
        for rec in self:
            contract_hours = 0
            attendances = self.env['resource.calendar.attendance'].search(
                [('calendar_id', '=', rec.id)])
            if attendances:
                for attendance in attendances:
                    contract_hours += attendance.hour_to - attendance.hour_from
            rec.contract_hours = contract_hours