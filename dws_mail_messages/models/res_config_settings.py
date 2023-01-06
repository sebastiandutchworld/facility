
from odoo import _, fields, models


###################
# Config Settings #
###################
class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    messages_easy_text_preview = fields.Integer(
        string="Text preview length",
        config_parameter="cetmix.messages_easy_text_preview",
    )
    messages_easy_color_note = fields.Char(
        string="Note Background",
        config_parameter="cetmix.messages_easy_color_note",
        help="Background color for internal notes in HTML format (e.g. #fbd78b)",
    )
    messages_easy_empty_trash = fields.Integer(
        string="Empty trash in (days)",
        config_parameter="cetmix.messages_easy_empty_trash",
        default=0,
    )

    def action_configure_cron(self):
        return {
            "name": _("Edit cron"),
            "views": [(False, "form")],
            "res_model": "ir.cron",
            "res_id": self.env.ref(
                "prt_mail_messages.ir_cron_ptr_mail_messages_action_unlink"
            ).id,
            "type": "ir.actions.act_window",
            "target": "new",
        }
