# Copyright 2026 Odoo-Eggs (Ahmed Foudhaili)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Tunisia - FODEC Tax",
    "summary": "Tunisian FODEC tax (1%) on sales, with VAT computed on the "
    "price plus FODEC",
    "version": "18.0.1.0.0",
    "category": "Accounting/Localizations",
    "website": "https://github.com/Odoo-Eggs/odooeggs-addons",
    "author": "Odoo-Eggs",
    "support": "support@eggsforge.com",
    "license": "LGPL-3",
    "countries": ["tn"],
    "depends": ["account", "l10n_tn"],
    "data": [
        "data/tax_report.xml",
    ],
    "images": [
        "static/description/banner.gif",
        "static/description/images/screenshot/invoice_fodec.png",
        "static/description/images/screenshot/product_taxes.png",
        "static/description/images/screenshot/journal_items.png",
        "static/description/images/screenshot/fodec_tax_config.png",
    ],
    "post_init_hook": "_l10n_tn_fodec_post_init",
    "installable": True,
}
