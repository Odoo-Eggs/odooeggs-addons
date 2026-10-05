# Copyright 2026 Odoo-Eggs (Ahmed Foudhaili)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("tn", "account.tax.group")
    def _get_tn_fodec_account_tax_group(self):
        return self._parse_csv("tn", "account.tax.group", module="l10n_tn_fodec")

    @template("tn", "account.tax")
    def _get_tn_fodec_account_tax(self):
        tax_data = self._parse_csv("tn", "account.tax", module="l10n_tn_fodec")
        self._deref_account_tags("tn", tax_data)
        return tax_data

    def _get_tn_fodec_fiscal_position_tax_ids(self):
        """FODEC mappings only, by fiscal position: {xmlid: [commands]}."""
        data = self._parse_csv("tn", "account.fiscal.position", module="l10n_tn_fodec")
        return {xmlid: values.get("tax_ids", []) for xmlid, values in data.items()}

    @template("tn", "account.fiscal.position")
    def _get_tn_fodec_account_fiscal_position(self):
        # Template values are merged with dict.update(): returning only the
        # FODEC mappings would replace the VAT mappings of l10n_tn.
        base = self._parse_csv("tn", "account.fiscal.position", module="l10n_tn")
        return {
            xmlid: {"tax_ids": base.get(xmlid, {}).get("tax_ids", []) + tax_ids}
            for xmlid, tax_ids in self._get_tn_fodec_fiscal_position_tax_ids().items()
        }

    def _l10n_tn_fodec_load(self):
        """Create what is missing on a company that already has the chart."""
        missing = {
            model: {
                xmlid: values
                for xmlid, values in data.items()
                if not self.ref(xmlid, raise_if_not_found=False)
            }
            for model, data in (
                ("account.tax.group", self._get_tn_fodec_account_tax_group()),
                ("account.tax", self._get_tn_fodec_account_tax()),
            )
        }
        fiscal_positions = {}
        for xmlid, tax_ids in self._get_tn_fodec_fiscal_position_tax_ids().items():
            position = self.ref(xmlid, raise_if_not_found=False)
            if not position:
                continue
            new = []
            for command in tax_ids:
                tax = self.ref(command[2]["tax_src_id"], raise_if_not_found=False)
                # A tax that does not exist yet cannot be mapped yet.
                if not tax or tax not in position.tax_ids.tax_src_id:
                    new.append(command)
            if new:
                fiscal_positions[xmlid] = {"tax_ids": new}
        self._load_data({**missing, "account.fiscal.position": fiscal_positions})
