{
    "name": "DWS Mail Debrand",
    "summary": """Remove Odoo branding in sent emails and the buttons in the emails
    """,
    "version": "14.0.1.0.0",
    "website": "dutchworld.nl",
    "author": """Dutchworld Solutions""",
    "license": "AGPL-3",
    'data': [
        'views/views.xml',
    ],
    "installable": True,
    "depends": ["mail","sale"],
}
