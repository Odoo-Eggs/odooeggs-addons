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

    @template("tn", "account.tax")
    def _get_tn_stamp_account_tax(self):
        # Template values are merged field by field: only the per-invoice
        # options and the sale distribution of the l10n_tn stamps change.
        tax_data = self._parse_csv("tn", "account.tax", module="l10n_tn_stamp")
        self._deref_account_tags("tn", tax_data)
        return tax_data

    def _get_tn_stamp_fiscal_positions(self):
        return self._parse_csv("tn", "account.fiscal.position", module="l10n_tn_stamp")

    def _get_chart_template_data(self, template_code):
        # The fiscal position mappings are added after the merge: a template
        # function returning "tax_ids" would replace the mappings of l10n_tn
        # and of the other modules (l10n_tn_fodec) instead of adding to them.
        data = super()._get_chart_template_data(template_code)
        if template_code == "tn":
            positions = data["account.fiscal.position"]
            for xmlid, values in self._get_tn_stamp_fiscal_positions().items():
                if xmlid in positions:
                    positions[xmlid].setdefault("tax_ids", []).extend(values["tax_ids"])
                else:
                    positions[xmlid] = values
        return data

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
            for line in stamp_sale.repartition_line_ids.filtered(
                lambda line: line.repartition_type == "tax"
            ):
                sign = "+" if line.document_type == "invoice" else "-"
                values = {"tag_ids": [Command.set(mapper(sign + "stamp_sale_due"))]}
                if account:
                    values["account_id"] = account.id
                line.write(values)

        positions = {}
        for xmlid, values in self._get_tn_stamp_fiscal_positions().items():
            position = self.ref(xmlid, raise_if_not_found=False)
            if not position:
                positions[xmlid] = values
                continue
            new = [
                command
                for command in values["tax_ids"]
                if self.ref(command[2]["tax_src_id"]) not in position.tax_ids.tax_src_id
            ]
            if new:
                positions[xmlid] = {"tax_ids": new}
        if positions:
            self._load_data({"account.fiscal.position": positions})

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
