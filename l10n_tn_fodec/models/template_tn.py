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
        # Since 19.0 the export exemption is a replacement tax (FODEC 0%) linked
        # to the export fiscal position: no fiscal position data to merge.
        tax_data = self._parse_csv("tn", "account.tax", module="l10n_tn_fodec")
        self._deref_account_tags("tn", tax_data)
        return tax_data

    def _l10n_tn_fodec_load(self):
        """Create what is missing on a company that already has the chart."""
        self._load_data(
            {
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
        )
