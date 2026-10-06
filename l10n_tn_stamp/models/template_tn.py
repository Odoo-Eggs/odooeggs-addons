# Copyright 2026 Odoo-Eggs (Ahmed Foudhaili)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
import logging

from odoo import Command, models

from odoo.addons.account.models.chart_template import template

_logger = logging.getLogger(__name__)

STAMP_SALE = "l10n_tn_tax_vat_sale_tax_stamp"
STAMP_PURCHASE = "l10n_tn_tax_vat_purchase_tax_stamp"


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("tn", "account.tax.group")
    def _get_tn_stamp_account_tax_group(self):
        # l10n_tn names the group "Fiscal Timbre" in English
        return self._parse_csv("tn", "account.tax.group", module="l10n_tn_stamp")

    @template("tn", "account.fiscal.position")
    def _get_tn_stamp_account_fiscal_position(self):
        return self._parse_csv("tn", "account.fiscal.position", module="l10n_tn_stamp")

    @template("tn", "account.tax")
    def _get_tn_stamp_account_tax(self):
        # Template values are merged field by field: only the per-invoice
        # options and the sale distribution of the l10n_tn stamps change.
        # Since 19.0 the exemptions are replacement taxes (stamp of 0) linked to
        # the export and public sector fiscal positions.
        tax_data = self._parse_csv("tn", "account.tax", module="l10n_tn_stamp")
        self._deref_account_tags("tn", tax_data)
        return tax_data

    def _l10n_tn_stamp_load(self):
        """Configure the stamp on a company that already has the chart.
        Running it again changes nothing."""
        company = self.env.company
        stamp_sale = self.ref(STAMP_SALE, raise_if_not_found=False)
        stamp_purchase = self.ref(STAMP_PURCHASE, raise_if_not_found=False)
        stamps = (stamp_sale or self.env["account.tax"]) | (
            stamp_purchase or self.env["account.tax"]
        )
        if not stamps:
            return
        stamps.write({"auto_tax": True, "auto_tax_on_refund": False})

        for xmlid, values in self._get_tn_stamp_account_tax_group().items():
            group = self.ref(xmlid, raise_if_not_found=False)
            if group:
                group.with_context(lang="en_US").name = values["name"]
                group.update_field_translations(
                    "name",
                    {
                        lang: values[f"name@{lang.split('_')[0]}"]
                        for lang, _name in self.env["res.lang"].get_installed()
                        if f"name@{lang.split('_')[0]}" in values
                    },
                )

        if stamp_sale:
            account = self.ref("l10n_tn_4371", raise_if_not_found=False)
            mapper = self._get_tag_mapper(company.account_fiscal_country_id.id)
            values = {"tag_ids": [Command.set(mapper("stamp_sale_due"))]}
            if account:
                values["account_id"] = account.id
            stamp_sale.repartition_line_ids.filtered(
                lambda line: line.repartition_type == "tax"
            ).write(values)

        # Public sector position and stamps of 0 (exemptions), if missing.
        new_taxes = {
            xmlid: values
            for xmlid, values in self._get_tn_stamp_account_tax().items()
            if xmlid not in (STAMP_SALE, STAMP_PURCHASE)
            and not self.ref(xmlid, raise_if_not_found=False)
        }
        new_positions = {
            xmlid: values
            for xmlid, values in self._get_tn_stamp_account_fiscal_position().items()
            if not self.ref(xmlid, raise_if_not_found=False)
        }
        if new_taxes or new_positions:
            self._load_data(
                {"account.fiscal.position": new_positions, "account.tax": new_taxes}
            )

        # A stamp left in the taxes of a product would be added once per line
        # on top of the stamp added once per invoice.
        products = (
            self.env["product.template"]
            .with_context(active_test=False)
            .search(
                [
                    "|",
                    ("taxes_id", "in", stamps.ids),
                    ("supplier_taxes_id", "in", stamps.ids),
                ]
            )
        )
        if products:
            products.write(
                {
                    "taxes_id": [Command.unlink(tax.id) for tax in stamps],
                    "supplier_taxes_id": [Command.unlink(tax.id) for tax in stamps],
                }
            )
            _logger.info(
                "%s: fiscal stamp removed from the taxes of %s product(s)",
                company.name,
                len(products),
            )
