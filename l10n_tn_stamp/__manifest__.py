# Copyright 2026 Odoo-Eggs (Ahmed Foudhaili)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Tunisia - Fiscal Stamp",
    "summary": "Tunisian fiscal stamp (droit de timbre): once per invoice, "
    "right account, tax report line, exemptions",
    "version": "18.0.1.0.0",
    "category": "Accounting/Localizations",
    "website": "https://github.com/Odoo-Eggs/odooeggs-addons",
    "author": "Odoo-Eggs",
    "support": "support@eggsforge.com",
    "license": "LGPL-3",
    "countries": ["tn"],
    "depends": ["account", "l10n_tn", "tax_auto_on_invoice"],
    "data": [
        "data/tax_report.xml",
        "views/res_config_settings_views.xml",
    ],
    "images": [
        "static/description/banner.gif",
        "static/description/images/screenshot/invoice_stamp_once.png",
        "static/description/images/screenshot/journal_items.png",
        "static/description/images/screenshot/public_sector.png",
        "static/description/images/screenshot/settings_mention.png",
    ],
    "post_init_hook": "_l10n_tn_stamp_post_init",
    "installable": True,
}
