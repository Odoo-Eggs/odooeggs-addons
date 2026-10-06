# Copyright 2026 Odoo-Eggs (Ahmed Foudhaili)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountTax(models.Model):
    _inherit = "account.tax"

    auto_tax = fields.Boolean(
        string="Add once per invoice",
        help="The tax is added automatically to every invoice of its type "
        "(sale or purchase), once per document and not once per line. "
        "Typical use: fiscal stamp (timbre fiscal), stamp duty.",
    )
    auto_tax_on_refund = fields.Boolean(
        string="Also on credit notes",
        help="Also add the tax to credit notes.",
    )

    @api.constrains("auto_tax", "amount_type")
    def _check_auto_tax_amount_type(self):
        for tax in self:
            if tax.auto_tax and tax.amount_type != "fixed":
                raise ValidationError(
                    _(
                        "The tax '%s' can be added once per invoice only if "
                        "its computation is 'Fixed'.",
                        tax.name,
                    )
                )
