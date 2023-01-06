from odoo import fields, models


#################
# Author assign #
#################
class MessagePartnerAssign(models.TransientModel):
    _name = "cx.message.partner.assign.wiz"
    _description = "Assign Partner to Messages"

    name = fields.Char(string="Name")
    email = fields.Char(string="Email")
    same_email = fields.Boolean(
        string="Match Email",
        default=True,
        help="Show Partners with same email address only",
    )
    partner_id = fields.Many2one(string="Assign To", comodel_name="res.partner")
