# Copyright 2026 Odoo-Eggs (Ahmed Foudhaili)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestTaxAutoOnInvoice(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stamp_sale = cls._create_stamp_tax("sale", cls.company_data["default_account_tax_sale"])
        cls.stamp_purchase = cls._create_stamp_tax(
            "purchase", cls.company_data["default_account_tax_purchase"]
        )

    @classmethod
    def _create_stamp_tax(cls, type_tax_use, account):
        def repartition():
            return [
                Command.create({"repartition_type": "base"}),
                Command.create({"repartition_type": "tax", "account_id": account.id}),
            ]

        return cls.env["account.tax"].create(
            {
                "name": f"Stamp {type_tax_use}",
                "amount_type": "fixed",
                "amount": 1.0,
                "type_tax_use": type_tax_use,
                "auto_tax": True,
                "invoice_repartition_line_ids": repartition(),
                "refund_repartition_line_ids": repartition(),
            }
        )

    def _invoice(self, move_type="out_invoice", quantities=(3, 5), **kwargs):
        tax = self.tax_sale_a if move_type.startswith("out_") else self.tax_purchase_a
        return self._create_invoice(
            move_type=move_type,
            invoice_line_ids=[
                self._prepare_invoice_line(price_unit=100.0, quantity=qty, tax_ids=tax)
                for qty in quantities
            ],
            **kwargs,
        )

    def _stamp_lines(self, move):
        return move.line_ids.filtered(lambda line: line.tax_line_id.auto_tax)

    def _assert_stamp(self, move, balance, amount_currency=None):
        stamp = self._stamp_lines(move)
        self.assertEqual(len(stamp), 1, "One stamp line per invoice")
        self.assertAlmostEqual(stamp.balance, balance)
        if amount_currency is not None:
            self.assertAlmostEqual(stamp.amount_currency, amount_currency)
        self.assertAlmostEqual(move.tax_totals["total_amount_currency"], move.amount_total)

    def test_out_invoice_once_per_invoice(self):
        invoice = self._invoice()
        self._assert_stamp(invoice, -1.0)
        # 800 untaxed + 15% VAT + 1 stamp, the VAT base is not affected.
        self.assertAlmostEqual(invoice.amount_untaxed, 800.0)
        self.assertAlmostEqual(invoice.amount_total, 921.0)
        invoice.action_post()
        self._assert_stamp(invoice, -1.0)
        self.assertEqual(invoice.payment_state, "not_paid")

    def test_in_invoice(self):
        bill = self._invoice("in_invoice")
        self._assert_stamp(bill, 1.0)
        self.assertNotIn(self.stamp_sale, bill.line_ids.tax_line_id)

    def test_refund_option(self):
        refund = self._invoice("out_refund")
        self.assertFalse(self._stamp_lines(refund))
        self.stamp_sale.auto_tax_on_refund = True
        refund = self._invoice("out_refund")
        self._assert_stamp(refund, 1.0)

    def test_fiscal_position_exemption(self):
        exempt = self.env["account.fiscal.position"].create(
            {
                "name": "Stamp exempt",
                "tax_ids": [Command.create({"tax_src_id": self.stamp_sale.id})],
            }
        )
        invoice = self._invoice(fiscal_position_id=exempt.id)
        self.assertFalse(self._stamp_lines(invoice))
        invoice.fiscal_position_id = False
        self._assert_stamp(invoice, -1.0)
        invoice.fiscal_position_id = exempt
        self.assertFalse(self._stamp_lines(invoice))

    def test_no_product_line(self):
        invoice = self._invoice()
        invoice.invoice_line_ids = [Command.clear()]
        self.assertFalse(invoice.line_ids)
        empty = self._create_invoice(invoice_line_ids=[])
        self.assertFalse(empty.line_ids)

    def test_lines_change(self):
        invoice = self._invoice(quantities=(1,))
        self._assert_stamp(invoice, -1.0)
        invoice.invoice_line_ids = [
            Command.create({"name": "extra", "price_unit": 50.0, "quantity": 4, "tax_ids": []})
        ]
        self._assert_stamp(invoice, -1.0)
        self.assertAlmostEqual(invoice.amount_total, 100.0 + 15.0 + 200.0 + 1.0)

    def test_foreign_currency(self):
        currency = self.setup_other_currency("EUR")  # 2 EUR = 1 company currency in 2017
        invoice = self._invoice(currency_id=currency.id, invoice_date="2017-06-01")
        self._assert_stamp(invoice, -1.0, amount_currency=-2.0)

    def test_form(self):
        with Form(self.env["account.move"].with_context(default_move_type="out_invoice")) as move_form:
            move_form.partner_id = self.partner_a
            move_form.invoice_date = "2019-01-01"
            for qty in (2, 7):
                with move_form.invoice_line_ids.new() as line_form:
                    line_form.product_id = self.product_a
                    line_form.quantity = qty
        invoice = move_form.record
        self._assert_stamp(invoice, -1.0)

    def test_other_company(self):
        company_2 = self.setup_other_company()["company"]
        invoice = (
            self.env["account.move"]
            .with_company(company_2)
            .create(
                {
                    "move_type": "out_invoice",
                    "partner_id": self.partner_a.id,
                    "invoice_date": "2019-01-01",
                    "invoice_line_ids": [Command.create({"name": "line", "price_unit": 10.0})],
                }
            )
        )
        self.assertFalse(self._stamp_lines(invoice))

    def test_only_fixed_taxes(self):
        with self.assertRaises(ValidationError):
            self.tax_sale_a.auto_tax = True
