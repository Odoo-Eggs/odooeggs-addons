# Copyright 2026 Odoo-Eggs (Ahmed Foudhaili)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from contextlib import contextmanager

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_auto_tax_product_lines(self):
        """Product lines used as base lines, same selection as
        `_get_rounded_base_and_tax_lines`."""
        self.ensure_one()
        lines = self.line_ids if self.id else self.invoice_line_ids
        return lines.filtered(lambda line: line.display_type == "product")

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
            *AccountTax._check_company_domain(self.company_id),
        ]
        if self.move_type in ("out_refund", "in_refund"):
            domain.append(("auto_tax_on_refund", "=", True))
        return self.fiscal_position_id.map_tax(AccountTax.search(domain))

    def _prepare_auto_tax_base_line_for_taxes_computation(self, taxes):
        """Single base line carrying the per-invoice taxes.

        The base is 0 and the quantity is the currency rate, so that the
        fixed amount of the tax is expressed in the company currency.
        """
        self.ensure_one()
        rate = self.invoice_currency_rate or 1.0
        return self.env["account.tax"]._prepare_base_line_for_taxes_computation(
            self.env["account.move.line"],
            id="auto_tax",
            tax_ids=taxes,
            price_unit=0.0,
            quantity=rate,
            currency_id=self.currency_id,
            rate=rate,
            sign=self.direction_sign,
            special_type="auto_tax",
            is_refund=self.move_type in ("out_refund", "in_refund"),
            tax_tag_invert=self.is_inbound(),
            partner_id=self.commercial_partner_id,
            account_id=self._get_auto_tax_product_lines()[:1].account_id,
        )

    def _get_rounded_base_and_tax_lines(self, round_from_tax_lines=True):
        base_lines, tax_lines = super()._get_rounded_base_and_tax_lines(
            round_from_tax_lines=round_from_tax_lines
        )
        taxes = self._get_auto_taxes()
        if taxes:
            AccountTax = self.env["account.tax"]
            auto_tax_line = self._prepare_auto_tax_base_line_for_taxes_computation(taxes)
            AccountTax._add_tax_details_in_base_lines([auto_tax_line], self.company_id)
            base_lines.append(auto_tax_line)
            AccountTax._round_base_lines_tax_details(
                base_lines,
                self.company_id,
                tax_lines=tax_lines if self.id and round_from_tax_lines else [],
            )
        return base_lines, tax_lines

    @contextmanager
    def _sync_tax_lines(self, container):
        with super()._sync_tax_lines(container):
            yield
        # The standard sync only reacts to changes of the base lines. Add or
        # remove the per-invoice taxes when they no longer match the invoice
        # (fiscal position, credit note, last line removed...). This runs
        # before the payment terms are synced, so the move stays balanced.
        for move in container["records"]:
            if move.state == "draft" and move.is_invoice():
                expected = move._get_auto_taxes().filtered("auto_tax")
                present = move.line_ids.tax_line_id.filtered("auto_tax")
                if expected != present:
                    move._auto_tax_recompute_tax_lines()

    def _auto_tax_recompute_tax_lines(self):
        """Recompute all the tax lines, like `_sync_tax_lines` does."""
        self.ensure_one()
        AccountTax = self.env["account.tax"]
        base_lines, tax_lines = self._get_rounded_base_and_tax_lines(
            round_from_tax_lines=False
        )
        AccountTax._add_accounting_data_in_base_lines_tax_details(
            base_lines, self.company_id, include_caba_tags=self.always_tax_exigible
        )
        tax_results = AccountTax._prepare_tax_lines(
            base_lines, self.company_id, tax_lines=tax_lines
        )
        for base_line, values in tax_results["base_lines_to_update"]:
            base_line["record"].write(values)
        for tax_line_vals, _grouping_key, values in tax_results["tax_lines_to_update"]:
            tax_line_vals["record"].write(values)
        to_delete = self.env["account.move.line"].union(
            *(tax_line_vals["record"] for tax_line_vals in tax_results["tax_lines_to_delete"])
        )
        to_delete.with_context(dynamic_unlink=True).unlink()
        self.env["account.move.line"].create(
            [
                {**tax_line_vals, "display_type": "tax", "move_id": self.id}
                for tax_line_vals in tax_results["tax_lines_to_add"]
            ]
        )
