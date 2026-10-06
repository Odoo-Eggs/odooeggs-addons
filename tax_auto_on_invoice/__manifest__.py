# Copyright 2026 Odoo-Eggs (Ahmed Foudhaili)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Fiscal Stamp per Invoice",
    "summary": "Add a fixed tax (fiscal stamp, stamp duty) once per invoice, "
    "not once per line",
    "version": "16.0.1.0.0",
    "category": "Accounting/Accounting",
    "website": "https://github.com/Odoo-Eggs/odooeggs-addons",
    "author": "Odoo-Eggs",
    "support": "support@eggsforge.com",
    "license": "LGPL-3",
    "depends": ["account"],
    "data": [
        "views/account_tax_views.xml",
    ],
    "images": [
        "static/description/images/screenshot/invoice_stamp_once.png",
        "static/description/images/screenshot/stamp_tax_config.png",
        "static/description/images/screenshot/journal_items.png",
    ],
    "installable": True,
}
