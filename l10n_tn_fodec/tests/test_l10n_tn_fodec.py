# Copyright 2026 Odoo-Eggs (Ahmed Foudhaili)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.l10n_tn_fodec import _l10n_tn_fodec_post_init

# Rule checked in the Journal officiel (JORT), see readme/CONTEXT.md:
# FODEC = 1% of the turnover excluding VAT (LF 2000 art. 37, LF 2011 art. 15),
# and the VAT base includes the other taxes (VAT code art. 6 I).


@tagged("post_install", "-at_install")
class TestL10nTnFodec(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("tn")
    def setUpClass(cls):
        super().setUpClass()
        cls.chart = cls.env["account.chart.template"].with_company(cls.env.company)
        cls.fodec_sale = cls.chart.ref("l10n_tn_fodec_tax_sale")
        cls.fodec_purchase = cls.chart.ref("l10n_tn_fodec_tax_purchase")
        cls.vat_sale = cls.chart.ref("l10n_tn_tax_vat_sale_19")
        cls.vat_sale_0 = cls.chart.ref("l10n_tn_tax_vat_sale_0")
        cls.vat_purchase = cls.chart.ref("l10n_tn_tax_vat_purchase_19_other_local")
        cls.fp_export = cls.chart.ref("l10n_tn_fp_template_export")
        cls.fp_exemption = cls.chart.ref("fiscal_position_template_exo")
        cls.product_fodec = cls._create_product(
            name="Paint", taxes_id=cls.fodec_sale | cls.vat_sale
        )
        # The amounts below are FODEC + VAT only: no fiscal stamp added once per
        # invoice (l10n_tn_stamp turns it on), except in test_fiscal_stamp.
        if "auto_tax" in cls.env["account.tax"]._fields:
            (
                cls.chart.ref("l10n_tn_tax_vat_sale_tax_stamp")
                | cls.chart.ref("l10n_tn_tax_vat_purchase_tax_stamp")
            ).auto_tax = False

    def _sale_invoice(self, move_type="out_invoice", **kwargs):
        return self._create_invoice(
            move_type=move_type,
            invoice_line_ids=[
                self._prepare_invoice_line(product_id=self.product_fodec, price_unit=1000.0)
            ],
            post=True,
            **kwargs,
        )

    def _tax_balance(self, move, tax):
        return sum(move.line_ids.filtered(lambda line: line.tax_line_id == tax).mapped("balance"))

    def test_taxes(self):
        self.assertEqual(self.fodec_sale.amount, 1.0)
        self.assertEqual(self.fodec_sale.amount_type, "percent")
        self.assertTrue(self.fodec_sale.include_base_amount)
        self.assertLess(self.fodec_sale.sequence, self.vat_sale.sequence)
        self.assertTrue(self.vat_sale.is_base_affected)
        self.assertEqual(self.fodec_purchase.type_tax_use, "purchase")
        self.assertFalse(self.fodec_purchase.invoice_repartition_line_ids.account_id)

    def test_sale_invoice(self):
        """FODEC = 1% of the price, VAT on price + FODEC."""
        move = self._sale_invoice()
        self.assertAlmostEqual(move.amount_untaxed, 1000.0)
        self.assertAlmostEqual(self._tax_balance(move, self.fodec_sale), -10.0)
        self.assertAlmostEqual(self._tax_balance(move, self.vat_sale), -191.9)
        self.assertAlmostEqual(move.amount_total, 1201.9)
        fodec_line = move.line_ids.filtered(lambda line: line.tax_line_id == self.fodec_sale)
        self.assertEqual(fodec_line.account_id, self.chart.ref("l10n_tn_43678"))
        # The FODEC amount is part of the VAT base, also in the tax report.
        self.assertEqual(
            sorted(fodec_line.tax_tag_ids.mapped("name")),
            ["fodec_sale_due", "sale_19_base_amount_tag"],
        )
        product_line = move.invoice_line_ids
        self.assertIn("fodec_sale_base", product_line.tax_tag_ids.mapped("name"))
        # The FODEC is shown before the VAT in the invoice totals.
        groups = move.tax_totals["subtotals"][0]["tax_groups"]
        self.assertEqual(groups[0]["id"], self.fodec_sale.tax_group_id.id)

    def test_refund(self):
        move = self._sale_invoice(move_type="out_refund")
        self.assertAlmostEqual(self._tax_balance(move, self.fodec_sale), 10.0)
        self.assertAlmostEqual(self._tax_balance(move, self.vat_sale), 191.9)
        fodec_line = move.line_ids.filtered(lambda line: line.tax_line_id == self.fodec_sale)
        self.assertEqual(
            sorted(fodec_line.tax_tag_ids.mapped("name")),
            ["fodec_sale_due", "sale_19_base_amount_tag"],
        )

    def test_export(self):
        """Exported products are exempt from FODEC (LF 2000 art. 36)."""
        # since 19.0: replaced by FODEC 0% (a tax cannot be mapped to nothing)
        fodec_export = self.chart.ref("l10n_tn_fodec_tax_sale_export")
        self.assertEqual(
            self.fp_export.map_tax(self.fodec_sale | self.vat_sale),
            fodec_export | self.vat_sale_0,
        )
        move = self._sale_invoice(fiscal_position_id=self.fp_export.id)
        self.assertEqual(move.invoice_line_ids.tax_ids, fodec_export | self.vat_sale_0)
        self.assertAlmostEqual(move.amount_total, 1000.0)

    def test_vat_exemption_keeps_fodec(self):
        """A VAT exemption does not exempt from FODEC."""
        move = self._sale_invoice(fiscal_position_id=self.fp_exemption.id)
        self.assertEqual(move.invoice_line_ids.tax_ids, self.fodec_sale | self.vat_sale_0)
        self.assertAlmostEqual(move.amount_total, 1010.0)

    def test_vendor_bill(self):
        """The FODEC paid to a manufacturer is a cost; VAT on price + FODEC."""
        move = self._create_invoice(
            move_type="in_invoice",
            invoice_line_ids=[
                self._prepare_invoice_line(
                    price_unit=1000.0, tax_ids=self.fodec_purchase | self.vat_purchase
                )
            ],
            post=True,
        )
        expense = move.invoice_line_ids.account_id
        self.assertAlmostEqual(
            sum(move.line_ids.filtered(lambda line: line.account_id == expense).mapped("balance")),
            1010.0,
        )
        self.assertAlmostEqual(self._tax_balance(move, self.vat_purchase), 191.9)
        self.assertAlmostEqual(move.amount_total, 1201.9)

    def test_export_keeps_vat_mappings(self):
        """The FODEC replacement tax is added to the export position next to the
        VAT replacement taxes of l10n_tn."""
        self.assertIn(self.chart.ref("l10n_tn_fodec_tax_sale_export"), self.fp_export.tax_ids)
        self.assertIn(self.vat_sale_0, self.fp_export.tax_ids)

    def test_tax_report_line(self):
        line = self.env.ref("l10n_tn_fodec.tax_report_line_fodec_sale")
        self.assertEqual(line.report_id, self.env.ref("l10n_tn.tax_report"))
        tags = line.expression_ids._get_matching_tags()
        self.assertEqual(
            sorted(tags.mapped("name")),
            ["fodec_sale_base", "fodec_sale_due"],
        )

    def test_existing_company(self):
        """A company with the Tunisian chart before the module was installed
        gets the FODEC taxes from the install hook, once."""
        company = self.setup_other_company(name="Existing TN company")["company"]
        chart = self.env["account.chart.template"].with_company(company)
        taxes = (
            chart.ref("l10n_tn_fodec_tax_sale")
            | chart.ref("l10n_tn_fodec_tax_purchase")
            | chart.ref("l10n_tn_fodec_tax_sale_export")
        )
        group = chart.ref("l10n_tn_fodec_tax_group")
        export = chart.ref("l10n_tn_fp_template_export")
        # Back to the state before the install of the module.
        self.env["ir.model.data"].search(
            [
                "|",
                "&", ("model", "=", "account.tax"), ("res_id", "in", taxes.ids),
                "&", ("model", "=", "account.tax.group"), ("res_id", "=", group.id),
            ]
        ).unlink()
        taxes.unlink()
        group.unlink()

        # Run as the install does (superuser, all companies), twice.
        _l10n_tn_fodec_post_init(self.env(su=True))
        _l10n_tn_fodec_post_init(self.env(su=True))

        fodec = chart.ref("l10n_tn_fodec_tax_sale")
        self.assertEqual(fodec.company_id, company)
        self.assertTrue(fodec.include_base_amount)
        self.assertEqual(
            self.env["account.tax"].search_count(
                [("company_id", "=", company.id), ("tax_group_id.name", "=", "FODEC 1%")]
            ),
            3,
        )
        fodec_export = chart.ref("l10n_tn_fodec_tax_sale_export")
        self.assertEqual(fodec_export.original_tax_ids, fodec)
        self.assertEqual(
            export.map_tax(fodec | chart.ref("l10n_tn_tax_vat_sale_19")),
            fodec_export | chart.ref("l10n_tn_tax_vat_sale_0"),
        )
        # The companies that had the module already are left unchanged.
        self.assertEqual(
            self.fodec_sale.replacing_tax_ids, self.chart.ref("l10n_tn_fodec_tax_sale_export")
        )

    def test_fiscal_stamp(self):
        """With tax_auto_on_invoice: one 1 DT stamp, outside the FODEC and
        VAT bases."""
        if "auto_tax" not in self.env["account.tax"]._fields:
            self.skipTest("tax_auto_on_invoice is not installed")
        stamp = self.chart.ref("l10n_tn_tax_vat_sale_tax_stamp")
        stamp.auto_tax = True
        move = self._sale_invoice()
        self.assertAlmostEqual(self._tax_balance(move, self.fodec_sale), -10.0)
        self.assertAlmostEqual(self._tax_balance(move, self.vat_sale), -191.9)
        self.assertAlmostEqual(self._tax_balance(move, stamp), -1.0)
        self.assertAlmostEqual(move.amount_total, 1202.9)
