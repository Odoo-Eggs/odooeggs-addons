# Copyright 2026 Odoo-Eggs (Ahmed Foudhaili)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_auto_tax_product_lines(self):
        self.ensure_one()
        return self.invoice_line_ids.filtered(lambda line: line.display_type == "product")

    def _get_auto_taxes(self):
        """Taxes to add once to this invoice (fiscal stamp...)."""
        self.ensure_one()
        AccountTax = self.env["account.tax"]
        if not self.is_invoice() or not self._get_auto_tax_product_lines():
            return AccountTax
        if self.state != "draft":
            # Never change the taxes of a posted invoice: only keep the
            # per-invoice taxes it already has.
            return self.line_ids.tax_line_id.filtered("auto_tax")
        domain = [
            ("auto_tax", "=", True),
            ("type_tax_use", "=", "sale" if self.is_sale_document() else "purchase"),
            ("company_id", "=", self.company_id.id),
        ]
        if self.move_type in ("out_refund", "in_refund"):
            domain.append(("auto_tax_on_refund", "=", True))
        return self.fiscal_position_id.map_tax(AccountTax.search(domain))

    def _prepare_auto_tax_base_line_dict(self, taxes):
        """Base line carrying the per-invoice taxes, for the tax totals.

        The price is 0 and the quantity is the currency rate, so that the
        fixed amount of the tax is expressed in the company currency.
        """
        self.ensure_one()
        lines = self._get_auto_tax_product_lines()
        rate = lines[:1].currency_rate or 1.0
        return self.env["account.tax"]._convert_to_tax_base_line_dict(
            None,
            partner=self.commercial_partner_id,
            currency=self.currency_id,
            taxes=taxes,
            price_unit=0.0,
            quantity=rate,
            account=lines[:1].account_id,
            is_refund=self.move_type in ("out_refund", "in_refund"),
            rate=rate,
            handle_price_include=False,
        )

    def _compute_tax_totals(self):
        super()._compute_tax_totals()
        for move in self:
            if not move.is_invoice(include_receipts=True):
                continue
            taxes = move._get_auto_taxes()
            if not taxes:
                continue
            sign = move.direction_sign
            base_lines = [
                line._convert_to_tax_base_line_dict()
                for line in move._get_auto_tax_product_lines()
            ]
            kwargs = {
                "currency": move.currency_id
                or move.journal_id.currency_id
                or move.company_id.currency_id,
            }
            if move.id:
                # same early payment discount lines as the standard
                base_lines += [
                    {
                        **line._convert_to_tax_base_line_dict(),
                        "handle_price_include": False,
                        "quantity": 1.0,
                        "price_unit": sign * line.amount_currency,
                    }
                    for line in move.line_ids.filtered(lambda line: line.display_type == "epd")
                ]
                kwargs["tax_lines"] = [
                    line._convert_to_tax_line_dict()
                    for line in move.line_ids.filtered(lambda line: line.display_type == "tax")
                ]
            base_lines.append(move._prepare_auto_tax_base_line_dict(taxes))
            move.tax_totals = self.env["account.tax"]._prepare_tax_totals(
                base_lines, **kwargs
            )
