# Copyright 2026 Odoo-Eggs (Ahmed Foudhaili)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import api, models
from odoo.tools import frozendict


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.depends(
        # standard dependencies
        "tax_ids",
        "currency_id",
        "partner_id",
        "analytic_distribution",
        "balance",
        "move_id.partner_id",
        "price_unit",
        "quantity",
        # the per-invoice taxes follow the invoice
        "move_id.invoice_line_ids",
        "move_id.fiscal_position_id",
        "move_id.move_type",
        "move_id.company_id",
    )
    def _compute_all_tax(self):
        super()._compute_all_tax()
        # In 17.0 the tax lines are computed line by line: the first product line
        # of the invoice also carries the taxes added once per invoice. The tax
        # lines are then grouped by key, so there is a single stamp line.
        for line in self:
            move = line.move_id
            if (
                line.display_type != "product"
                or not move.is_invoice()
                or line != move._get_auto_tax_product_lines()[:1]
            ):
                continue
            taxes = move._get_auto_taxes()
            if not taxes:
                continue
            sign = move.direction_sign
            rate = line.currency_rate or 1.0
            # Price 0, quantity = currency rate: the fixed amount is in the
            # company currency.
            result = taxes.compute_all(
                0.0,
                currency=line.currency_id,
                quantity=rate,
                partner=move.partner_id or line.partner_id,
                is_refund=line.is_refund,
                handle_price_include=False,
                include_caba_tags=move.always_tax_exigible,
                fixed_multiplicator=sign,
            )
            compute_all_tax = dict(line.compute_all_tax)
            for tax in result["taxes"]:
                if not tax["amount"]:
                    continue
                key = frozendict(
                    {
                        "tax_repartition_line_id": tax["tax_repartition_line_id"],
                        "group_tax_id": tax["group"] and tax["group"].id or False,
                        "account_id": tax["account_id"] or line.account_id.id,
                        "currency_id": line.currency_id.id,
                        "analytic_distribution": (
                            tax["analytic"] or not tax["use_in_tax_closing"]
                        )
                        and line.analytic_distribution,
                        "tax_ids": [(6, 0, tax["tax_ids"])],
                        "tax_tag_ids": [(6, 0, tax["tag_ids"])],
                        "partner_id": move.partner_id.id or line.partner_id.id,
                        "move_id": move.id,
                        "display_type": line.display_type,
                    }
                )
                values = compute_all_tax.get(key, {})
                compute_all_tax[key] = {
                    "name": tax["name"],
                    "balance": values.get("balance", 0.0) + tax["amount"] / rate,
                    "amount_currency": values.get("amount_currency", 0.0) + tax["amount"],
                    "tax_base_amount": values.get("tax_base_amount", 0.0),
                }
            line.compute_all_tax = compute_all_tax
            line.compute_all_tax_dirty = True
