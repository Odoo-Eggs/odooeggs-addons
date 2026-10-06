# Copyright 2026 Odoo-Eggs (Ahmed Foudhaili)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from markupsafe import Markup

from odoo import fields, models
from odoo.tools import is_html_empty

# CDET art. 127 (Finance Law for 2004, art. 95): wording of the law, in French.
STAMP_MENTION = Markup("<p>Droit de timbre payé sur déclaration</p>")


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_tn_stamp_invoice_mention = fields.Boolean(
        string="Print the stamp duty mention",
        compute="_compute_l10n_tn_stamp_invoice_mention",
        inverse="_inverse_l10n_tn_stamp_invoice_mention",
        help="Print « Droit de timbre payé sur déclaration » on the invoices that "
        "carry the fiscal stamp (stamp duty code, art. 127). It is the legal note "
        "of the sale stamp tax, which can also be edited on the tax.",
    )

    def _l10n_tn_stamp_sale_tax(self):
        self.ensure_one()
        return (
            self.env["account.chart.template"]
            .with_company(self.company_id)
            .ref("l10n_tn_tax_vat_sale_tax_stamp", raise_if_not_found=False)
        )

    def _compute_l10n_tn_stamp_invoice_mention(self):
        for config in self:
            tax = config._l10n_tn_stamp_sale_tax()
            config.l10n_tn_stamp_invoice_mention = bool(
                tax and not is_html_empty(tax.invoice_legal_notes)
            )

    def _inverse_l10n_tn_stamp_invoice_mention(self):
        for config in self:
            tax = config._l10n_tn_stamp_sale_tax()
            if not tax:
                continue
            if config.l10n_tn_stamp_invoice_mention:
                if is_html_empty(tax.invoice_legal_notes):
                    tax.invoice_legal_notes = STAMP_MENTION
            else:
                tax.invoice_legal_notes = False
