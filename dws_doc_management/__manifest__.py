# Copyright 2015 ABF OSIELL <https://osiell.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Customizations for Gearboks Documents",
    "version": "13.0.1.0.1",
    "author": "Dutchworld Solutions",
    "license": "AGPL-3",
    "website": "https://dutchworld.nl",
    "category": "Tools",
    "depends": ["base", "documents"],
    "data": [
        "views/document_customizations_view.xml",
        "views/assets.xml",
        "data/ir_cron.xml",
        "data/emails.xml"
    ],
    "application": True,
    "installable": True,
    'assets': {
        'web.assets_backend': [
            '/dws_doc_management/static/src/js/documents_inspector.js'
        ]
    }
}
