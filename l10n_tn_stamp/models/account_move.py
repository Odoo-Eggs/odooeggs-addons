# Copyright 2026 Odoo-Eggs (Ahmed Foudhaili)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import api, models
from odoo.tools import is_html_empty


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends("line_ids.tax_line_id")
    def _compute_taxes_legal_notes(self):
        # The standard only reads the taxes of the lines: the taxes added once
        # per invoice (fiscal stamp) are tax lines, their legal notes are added.
        super()._compute_taxes_legal_notes()
        for move in self:
            line_taxes = move.line_ids.tax_ids
            notes = [
                tax.invoice_legal_notes
                for tax in move.line_ids.tax_line_id.filtered("auto_tax")
                if tax not in line_taxes and not is_html_empty(tax.invoice_legal_notes)
            ]
            if notes:
                move.taxes_legal_notes = (move.taxes_legal_notes or "") + "".join(notes)
