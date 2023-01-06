from datetime import datetime

from odoo import api, fields, models
from odoo.exceptions import AccessError


#################
# Edit message #
#################
class MessageEdit(models.TransientModel):
    _name = "cx.message.edit.wiz"
    _description = "Edit Message or Note"

    def _get_message(self):
        if "message_edit_id" in self._context:
            message_id = self._context["message_edit_id"]
        else:
            active_ids = self._context.get("active_ids", False)
            if active_ids:
                message_id = active_ids[0]
            else:
                return False

        # To check direct context value
        if not message_id:
            return False
        return self.env["mail.message"].browse(message_id)

    message_id = fields.Many2one(
        string="Message", comodel_name="mail.message", default=_get_message
    )
    body = fields.Html(string="Message")
    can_edit = fields.Boolean(string="Can Edit", compute="_compute_can_edit")

    # -- Get message body
    @api.onchange("message_id")
    def message_change(self):
        self.body = self.message_id.body if self.message_id else False

    # -- Can edit message?
    @api.depends("message_id")
    def _compute_can_edit(self):
        if not self.message_id:
            self.can_edit = False
            return

        # Just in case)
        if not self.message_id.author_id:
            self.can_edit = False
            return

        # Superuser can edit everything:
        if self.env.is_superuser():
            self.can_edit = True
            return

        # Check access rule
        try:
            self.message_id.check_access_rule("write")
        except AccessError:
            self.can_edit = False
            return

        # Can edit
        can_edit = False

        # Check subtype.
        mt_note = self.env.ref("mail.mt_note").id
        mt_comment = self.env.ref("mail.mt_comment").id

        # Note
        if self.message_id.subtype_id.id == mt_note:
            # Can edit any note?
            if self.env.user.has_group("dws_mail_messages.group_notes_edit_all"):
                can_edit = True
                # Can edit own notes and is note author?
            elif (
                self.env.user.has_group("dws_mail_messages.group_notes_edit_own")
                and self.message_id.author_id.id == self.env.user.partner_id.id
            ):
                can_edit = True

        # Message
        elif self.message_id.subtype_id.id == mt_comment:
            # Can edit any message?
            if self.env.user.has_group("dws_mail_messages.group_messages_edit_all"):
                can_edit = True
            # Can edit own messages and is message author?
            if (
                self.env.user.has_group("dws_mail_messages.group_messages_edit_own")
                and self.message_id.author_id.id == self.env.user.partner_id.id
            ):
                can_edit = True
        # Other types are not editable
        else:
            self.can_edit = False

        # Return
        self.can_edit = can_edit

    # -- Save message
    def save(self):
        # To be 10000% sure!)
        if self.message_id and self.can_edit:
            self.message_id.write(
                {
                    "body": self.body,
                    "cx_edit_uid": self.env.user.id,
                    "cx_edit_date": datetime.now(),
                }
            )
