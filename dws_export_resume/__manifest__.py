# noinspection PyStatementEffect

{
    "name": "Gearboks print resume",
    "summary": "Export Resume for employees -> Task #2843",
    "version": "14.0.1.0.1",
    "author": "Dutchworld Solutions",
    "license": "AGPL-3",
    "website": "https://dutchworld.nl",
    "category": "Tools",
    "depends": ["base", "hr", "crm", "website"],
    "data": [
        "wizard/select_company.xml",
        "views/form_view.xml",
        "security/ir.model.access.csv"
    ],
    'assets': {
        'web.assets_backend': [
            '/dws_export_resume/static/src/js/select_company.js'
        ]
    },
    "application": True,
    "installable": True,
}

