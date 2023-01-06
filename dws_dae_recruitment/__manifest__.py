# Copyright 2015 ABF OSIELL <https://osiell.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Gearboks recruitment",
    "version": "14.0.1.0.1",
    "author": "Dutchworld Solutions",
    "license": "AGPL-3",
    "website": "https://dutchworld.nl",
    "category": "Tools",
    "depends": ["base", "dws_dae_custom","website","web","portal","hr_skills",'crm','website_hr_recruitment','hr_recruitment','w_open_many2many_tags','hr'],
    "data": [
        "views/assets.xml",
        "views/skill_line_editable.xml",
        "views/templates.xml",
        "views/jobs.xml",
        "views/resume_line.xml",
        "views/lead_views.xml",
        "views/hr_skills.xml",
        "views/recruitment.xml",
        "views/portal_templates.xml",
        "views/employee_views.xml",
        "security/ir.model.access.csv",
        "data/emails.xml",
        "data/ir_cron.xml"
    ],
    'qweb': [
            'static/src/xml/resume_templates.xml',
        ],
    "application": True,
    "installable": True,
    'assets': {
        'web.assets_frontend': [
            "/dws_dae_recruitment/static/src/js/skill_data.js",
            "/dws_dae_recruitment/static/src/js/resume_line.js",
            "/dws_dae_recruitment/static/src/js/skill_line.js",
            "/dws_dae_recruitment/static/src/scss/custom_style.scss"
        ],
        'web.assets_backend': [
        "/dws_dae_recruitment/static/src/js/resume_widget.js"
        ]
    }
}
