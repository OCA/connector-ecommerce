# © 2013 Camptocamp SA
# © 2018 FactorLibre
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from unittest import mock

import odoo.tests.common as common


class TestInvoiceEvent(common.TransactionCase):
    """Test if the events on the invoice are fired correctly"""

    def setUp(self):
        super(TestInvoiceEvent, self).setUp()
        self.invoice_model = self.env["account.move"]
        partner_model = self.env["res.partner"]
        partner = partner_model.create({"name": "Hodor"})
        product = self.env.ref("product.product_product_6")
        invoice_vals = {
            "partner_id": partner.id,
            "company_id": self.env.ref("base.main_company").id,
            "move_type": "out_invoice",
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "name": "LCD Screen",
                        "product_id": product.id,
                        "quantity": 5,
                        "price_unit": 200,
                    },
                )
            ],
        }
        self.invoice = self.invoice_model.create(invoice_vals)
        self.invoice._onchange_partner_id()

        # self.invoice = self.invoice_model.create(
        #     invoice._convert_to_write(invoice._cache)
        # )
        self.journal = self.env["account.journal"].search(
            [("type", "=", "bank"), ("company_id", "=", self.env.company.id)],
            limit=1,
        )

    def test_event_validated(self):
        """Test if the ``on_invoice_validated`` event is fired
        when an invoice is validated"""
        assert self.invoice, "The invoice has not been created"

        mock_method = "odoo.addons.component_event.models.base.Base._event"
        with mock.patch(mock_method) as mock_event:
            self.invoice.action_post()
            self.assertEqual(self.invoice.state, "posted")
            mock_event("on_invoice_validated").notify.assert_any_call(self.invoice)

    def test_event_paid(self):
        """Test if the ``on_invoice_paid`` event is fired
        when an invoice is paid"""
        assert self.invoice, "The invoice has not been created"

        mock_method = "odoo.addons.component_event.models.base.Base._event"
        with mock.patch(mock_method) as mock_event:
            self.assertEqual(self.invoice.state, "draft")
            self.invoice.action_post()
            self.assertEqual(self.invoice.state, "posted")
            register_payments = (
                self.env["account.payment.register"]
                .with_context(active_model="account.move", active_ids=self.invoice.ids)
                .create({"journal_id": self.journal.id})
            )
            register_payments._create_payments()
            self.assertEqual(self.invoice.payment_state, "paid")
            mock_event("on_invoice_paid").notify.assert_any_call(self.invoice)
