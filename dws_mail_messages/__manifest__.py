{
    "name": "DWS Mail Messages",
    "version": "14.0.1.0.1",
    "summary": """DWS Mail Messages""",

    "author": "Ivan Sokolov, Cetmix",
    "category": "Discuss",
    "license": "LGPL-3",
    "website": "https://cetmix.com",
    "description": """
 Show all messages, Show sent message, Reply to messages,
  Forward messages, Edit messages, Delete messages, Move messages, Quote messages
""",
    "depends": ["mail"],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "security/rules.xml",
        "data/data.xml",
        "data/data_cron.xml",
        "views/mail_message.xml",
        "views/conversation.xml",
        "views/partner.xml",
        "views/res_config_settings.xml",
        "views/actions.xml",
        "report/mail_message_paperformat.xml",
        "report/mail_message_report.xml",
        "wizard/message_edit.xml",
        "wizard/message_partner_assign.xml",
        "wizard/message_move.xml",
        "wizard/mail_compose_message.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "dws_mail_messages/static/src/js/list_mixin.js",
            "dws_mail_messages/static/src/js/mail_messages_update_view_list.js",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}
