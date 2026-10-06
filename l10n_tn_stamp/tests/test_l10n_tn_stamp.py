# Copyright 2026 Odoo-Eggs (Ahmed Foudhaili)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.l10n_tn_stamp import _l10n_tn_stamp_post_init

# Rule checked in the Journal officiel (JORT), see readme/DESCRIPTION.rst:
# stamp duty of 1.000 TND per invoice (stamp duty code, art. 117 I no. 6,
# Finance Law for 2023, art. 69); exports exempt (art. 118 no. 29); invoices paid
# by the State, local authorities and public bodies exempt (art. 118 no. 19).


@tagged("post_install", "-at_install")
class TestL10nTnStamp(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("tn")
    def setUpClass(cls):
        super().setUpClass()
        cls.chart = cls.env["account.chart.template"].with_company(cls.env.company)
        cls.stamp_sale = cls.chart.ref("l10n_tn_tax_vat_sale_tax_stamp")
        cls.stamp_purchase = cls.chart.ref("l10n_tn_tax_vat_purchase_tax_stamp")
        cls.vat_sale = cls.chart.ref("l10n_tn_tax_vat_sale_19")
        cls.vat_sale_0 = cls.chart.ref("l10n_tn_tax_vat_sale_0")
        cls.vat_purchase = cls.chart.ref("l10n_tn_tax_vat_purchase_19_other_local")
        cls.fp_export = cls.chart.ref("l10n_tn_fp_template_export")
        cls.fp_exemption = cls.chart.ref("fiscal_position_template_exo")
        cls.fp_public = cls.chart.ref("l10n_tn_stamp_fp_public")
        cls.account_4371 = cls.chart.ref("l10n_tn_4371")
        cls.account_6654 = cls.chart.ref("l10n_tn_6654")
        cls.product = cls._create_product(name="Olive oil", taxes_id=cls.vat_sale)

    def _sale_invoice(self, move_type="out_invoice", lines=3, quantity=5, **kwargs):
        return self._create_invoice(
            move_type=move_type,
            invoice_line_ids=[
                self._prepare_invoice_line(
                    product_id=self.product, price_unit=100.0, quantity=quantity
                )
                for _i in range(lines)
            ],
            post=True,
            **kwargs,
        )

    def _stamp_lines(self, move):
        return move.line_ids.filtered(lambda line: line.tax_line_id.auto_tax)

    def test_stamp_taxes(self):
        self.assertEqual(self.stamp_sale.amount_type, "fixed")
        self.assertAlmostEqual(self.stamp_sale.amount, 1.0)
        for tax in self.stamp_sale | self.stamp_purchase:
            self.assertTrue(tax.auto_tax)
            self.assertFalse(tax.auto_tax_on_refund)
        sale_lines = self.stamp_sale.repartition_line_ids.filtered(
            lambda line: line.repartition_type == "tax"
        )
        self.assertEqual(sale_lines.account_id, self.account_4371)
        self.assertEqual(
            sorted(sale_lines.tag_ids.mapped("name")), ["+stamp_sale_due", "-stamp_sale_due"]
        )
        purchase_lines = self.stamp_purchase.repartition_line_ids.filtered(
            lambda line: line.repartition_type == "tax"
        )
        self.assertEqual(purchase_lines.account_id, self.account_6654)

    def test_once_per_invoice(self):
        """3 lines of 5 units: one stamp of 1.000, the VAT base is not affected."""
        move = self._sale_invoice()
        stamp = self._stamp_lines(move)
        self.assertEqual(len(stamp), 1)
        self.assertEqual(stamp.tax_line_id, self.stamp_sale)
        self.assertEqual(stamp.account_id, self.account_4371)
        self.assertAlmostEqual(stamp.balance, -1.0)
        self.assertEqual(stamp.tax_tag_ids.mapped("name"), ["+stamp_sale_due"])
        self.assertAlmostEqual(move.amount_untaxed, 1500.0)
        self.assertAlmostEqual(move.amount_total, 1500.0 + 285.0 + 1.0)

    def test_refund_without_stamp(self):
        move = self._sale_invoice(move_type="out_refund")
        self.assertFalse(self._stamp_lines(move))

    def test_vendor_bill(self):
        move = self._create_invoice(
            move_type="in_invoice",
            invoice_line_ids=[
                self._prepare_invoice_line(price_unit=100.0, tax_ids=self.vat_purchase)
            ],
            post=True,
        )
        stamp = self._stamp_lines(move)
        self.assertEqual(stamp.tax_line_id, self.stamp_purchase)
        self.assertEqual(stamp.account_id, self.account_6654)
        self.assertAlmostEqual(stamp.balance, 1.0)
        self.assertAlmostEqual(move.amount_total, 120.0)

    def test_export_without_stamp(self):
        """Export invoices are exempt (art. 118 no. 29), and a foreign supplier
        does not charge the Tunisian stamp."""
        move = self._sale_invoice(fiscal_position_id=self.fp_export.id)
        self.assertFalse(self._stamp_lines(move))
        self.assertEqual(move.invoice_line_ids.tax_ids, self.vat_sale_0)
        bill = self._create_invoice(
            move_type="in_invoice",
            invoice_line_ids=[self._prepare_invoice_line(price_unit=100.0)],
            fiscal_position_id=self.fp_export.id,
            post=True,
        )
        self.assertFalse(self._stamp_lines(bill))
        # the VAT mappings of l10n_tn are kept
        self.assertEqual(self.fp_export.map_tax(self.vat_sale), self.vat_sale_0)

    def test_vat_exemption_keeps_stamp(self):
        move = self._sale_invoice(fiscal_position_id=self.fp_exemption.id)
        self.assertAlmostEqual(self._stamp_lines(move).balance, -1.0)

    def test_public_sector_without_stamp(self):
        """Invoices paid by the State and public bodies are exempt
        (art. 118 no. 19): no stamp, normal VAT, never applied automatically."""
        self.assertFalse(self.fp_public.auto_apply)
        self.assertEqual(self.fp_public.country_id.code, "TN")
        move = self._sale_invoice(fiscal_position_id=self.fp_public.id)
        self.assertFalse(self._stamp_lines(move))
        self.assertEqual(move.invoice_line_ids.tax_ids, self.vat_sale)

    def test_invoice_mention(self):
        """The mention is off by default; the setting writes it as the legal
        note of the sale stamp, printed on the invoices that carry the stamp."""
        mention = "Droit de timbre payé sur déclaration"
        move = self._sale_invoice()
        self.assertNotIn(mention, move.taxes_legal_notes or "")
        settings = self.env["res.config.settings"].create({})
        self.assertFalse(settings.l10n_tn_stamp_invoice_mention)
        settings.l10n_tn_stamp_invoice_mention = True
        settings.execute()
        move.invalidate_recordset(["taxes_legal_notes"])
        self.assertIn(mention, move.taxes_legal_notes)
        html = self.env["ir.actions.report"]._render_qweb_html(
            "account.report_invoice", move.ids
        )[0].decode()
        self.assertIn(mention, html)
        export = self._sale_invoice(fiscal_position_id=self.fp_export.id)
        self.assertNotIn(mention, export.taxes_legal_notes or "")
        settings = self.env["res.config.settings"].create({})
        self.assertTrue(settings.l10n_tn_stamp_invoice_mention)
        # the settings form opens through an onchange on a new record
        values = self.env["res.config.settings"].onchange(
            {}, [], {"company_id": {}, "l10n_tn_stamp_invoice_mention": {}}
        )["value"]
        self.assertTrue(values["l10n_tn_stamp_invoice_mention"])
        settings.l10n_tn_stamp_invoice_mention = False
        settings.execute()
        self.assertFalse(self.stamp_sale.invoice_legal_notes)

    def test_existing_company(self):
        """The hook configures a company that has the l10n_tn stamp as shipped,
        removes the stamp from the products, and changes nothing the 2nd time."""
        account_437 = self.chart.ref("l10n_tn_437")
        self.stamp_sale.write({"auto_tax": False, "invoice_legal_notes": False})
        self.stamp_purchase.auto_tax = False
        self.stamp_sale.repartition_line_ids.filtered(
            lambda line: line.repartition_type == "tax"
        ).write({"account_id": account_437.id, "tag_ids": [Command.clear()]})
        self.fp_export.tax_ids.filtered(
            lambda line: line.tax_src_id in (self.stamp_sale | self.stamp_purchase)
        ).unlink()
        self.fp_public.unlink()
        product = self._create_product(
            name="Stamped", taxes_id=self.vat_sale | self.stamp_sale
        )

        # hooks run as superuser at install
        _l10n_tn_stamp_post_init(self.env(su=True))
        self.test_stamp_taxes()
        # the product may also carry taxes of other companies: read them as superuser
        self.assertNotIn(self.stamp_sale, product.sudo().taxes_id)
        self.assertIn(self.vat_sale, product.sudo().taxes_id)
        self.assertEqual(
            self.fp_export.map_tax(self.stamp_sale | self.stamp_purchase),
            self.env["account.tax"],
        )
        fp_public = self.chart.ref("l10n_tn_stamp_fp_public")
        self.assertEqual(fp_public.map_tax(self.stamp_sale), self.env["account.tax"])

        mappings = self.fp_export.tax_ids
        # hooks run as superuser at install
        _l10n_tn_stamp_post_init(self.env(su=True))
        self.assertEqual(self.fp_export.tax_ids, mappings)
        self.assertEqual(
            self.env["account.fiscal.position"].search_count(
                [("name", "=", fp_public.name), ("company_id", "=", self.env.company.id)]
            ),
            1,
        )

    def test_tax_report_tag(self):
        """The stamp is tagged for the stamp line of the tax report."""
        line = self.env.ref("l10n_tn_stamp.tax_report_line_stamp")
        self.assertEqual(line.report_id, self.env.ref("l10n_tn.tax_report"))
        move = self._sale_invoice()
        tag = self._stamp_lines(move).tax_tag_ids
        self.assertEqual(tag.name, "+stamp_sale_due")
        self.assertEqual(line.expression_ids.formula, "stamp_sale_due")

    def test_with_fodec(self):
        """With l10n_tn_fodec: both modules add their mappings to the export
        position, and TTC = HT + FODEC + VAT(HT + FODEC) + 1.000."""
        fodec = self.chart.ref("l10n_tn_fodec_tax_sale", raise_if_not_found=False)
        if not fodec:
            self.skipTest("l10n_tn_fodec is not installed")
        self.assertEqual(
            self.fp_export.map_tax(fodec | self.stamp_sale | self.vat_sale), self.vat_sale_0
        )
        product = self._create_product(name="Paint", taxes_id=fodec | self.vat_sale)
        move = self._create_invoice(
            invoice_line_ids=[self._prepare_invoice_line(product_id=product, price_unit=1000.0)],
            post=True,
        )
        self.assertAlmostEqual(move.amount_total, 1000.0 + 10.0 + 191.9 + 1.0)
