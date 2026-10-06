# Copyright 2026 Odoo-Eggs (Ahmed Foudhaili)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from . import models


def _l10n_tn_stamp_post_init(env):
    """Configure the fiscal stamp of the companies that already use the
    Tunisian chart of accounts. New companies get it from the chart template."""
    companies = env["res.company"].search(
        [("chart_template", "=", "tn"), ("parent_id", "=", False)]
    )
    for company in companies:
        env["account.chart.template"].with_company(company)._l10n_tn_stamp_load()
