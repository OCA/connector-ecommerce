# -*- coding: utf-8 -*-
# © 2013 Camptocamp SA
# © 2018 FactorLibre
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import mock

import odoo.tests.common as common


class TestInvoiceEvent(common.TransactionCase):
    """ Test if the events on the invoice are fired correctly """

    def setUp(self):
        super(TestInvoiceEvent, self).setUp()
        self.invoice_model = self.env['account.invoice']
        invoice_line_model = self.env['account.invoice.line']
        partner_model = self.env['res.partner']
        partner = partner_model.create({'name': 'Hodor'})
        product = self.env.ref('product.product_product_6')
        invoice_vals = {'partner_id': partner.id,
                        'type': 'out_invoice',
                        'company_id': self.env.ref('base.main_company')
                        }
        invoice = self.invoice_model.new(invoice_vals)
        invoice._onchange_partner_id()

        self.invoice = self.invoice_model.create(
            invoice._convert_to_write(invoice._cache)
        )

        line_vals = {'name': "LCD Screen",
                     'product_id': product,
                     'quantity': 5,
                     'price_unit': 200,
                     'invoice_id': self.invoice,
                     }
        line = invoice_line_model.new(line_vals)
        line._onchange_product_id()
        invoice_line_model.create(
            line._convert_to_write(line._cache)
        )

    def test_event_validated(self):
        """ Test if the ``on_invoice_validated`` event is fired
        when an invoice is validated """
        assert self.invoice, "The invoice has not been created"

        mock_method = 'odoo.addons.component_event.models.base.Base._event'
        with mock.patch(mock_method) as mock_event:
            self.invoice.action_invoice_open()
            self.assertEqual(self.invoice.state, 'open')
            mock_event('on_invoice_validated').notify.assert_any_call(
                self.invoice)

    def test_event_paid(self):
        """ Test if the ``on_invoice_paid`` event is fired
        when an invoice is paid """
        assert self.invoice, "The invoice has not been created"

        mock_method = 'odoo.addons.component_event.models.base.Base._event'
        with mock.patch(mock_method) as mock_event:
            self.invoice.action_invoice_open()
            self.assertEqual(self.invoice.state, 'open')
            journal = self.env['account.journal'].search([], limit=1)

            self.invoice.pay_and_reconcile(
                journal,
                pay_amount=self.invoice.amount_total,
            )
            self.assertEqual(self.invoice.state, 'paid')
            mock_event('on_invoice_paid').notify.assert_any_call(
                self.invoice)
