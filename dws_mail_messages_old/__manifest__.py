{
    "name": "DWS Mail Messages",
    "version": "14.0.1.0.1",
    "summary": """DWS Mail Messages""",
    "category": "Discuss",
    "license": "LGPL-3",
    "website": "https://cetmix.com",
    "description": """
 Show all messages, Show sent message, Reply to messages,
  Forward messages, Edit messages, Delete messages, Move messages, Quote messages
""",
    "depends": ["base", "mail"],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "security/rules.xml",
        "data/data.xml",
        "views/mail_message.xml",
        "views/conversation.xml",
        "views/partner.xml",
        "views/res_config_settings.xml",
        "views/actions.xml",
        "views/templates.xml",
        "wizard/message_edit.xml",
        "wizard/message_partner_assign.xml",
        "wizard/message_move.xml",
        "wizard/mail_compose_message.xml",
    ],
    "qweb": [
        "static/src/xml/*.xml"
    ],
    'assets': {
        'web.assets_backend': [
            '/dws_mail_messages/static/src/css/message_reply.css',
            '/dws_mail_messages/static/src/js/list_model.js',
            '/dws_mail_messages/static/src/js/list_controller.js',
            '/dws_mail_messages/static/src/js/list_renderer.js',
            '/dws_mail_messages/static/src/components/message/message.js',
            '/dws_mail_messages/static/src/models/message/message.js'
        ]
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}
