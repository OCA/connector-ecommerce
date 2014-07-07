# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import unittest2
import mock
from functools import partial

import openerp.tests.common as common
from openerp import netsvc


class test_invoice_event(common.TransactionCase):
    """ Test if the events on the invoice are fired correctly """

    def setUp(self):
        super(test_invoice_event, self).setUp()
        cr, uid = self.cr, self.uid
        self.invoice_model = self.registry('account.invoice')
        partner_model = self.registry('res.partner')
        partner_id = partner_model.create(cr, uid, {'name': 'Hodor'})
        data_model = self.registry('ir.model.data')
        self.get_ref = partial(data_model.get_object_reference, cr, uid)
        product_id = self.get_ref('product', 'product_product_6')[1]
        invoice_vals = {'partner_id': partner_id,
                        'type': 'out_invoice',
                        'invoice_line': [(0, 0, {'name': "LCD Screen",
                                                 'product_id': product_id,
                                                 'quantity': 5,
                                                 'price_unit': 200})],
                        }
        onchange_res = self.invoice_model.onchange_partner_id(
            cr, uid, [], 'out_invoice', partner_id)
        invoice_vals.update(onchange_res['value'])
        invoice_id = self.invoice_model.create(cr, uid, invoice_vals)
        self.invoice = self.invoice_model.browse(cr, uid, invoice_id)

    def test_event_validated(self):
        """ Test if the ``on_invoice_validated`` event is fired
        when an invoice is validated """
        cr, uid = self.cr, self.uid
        assert self.invoice, "The invoice has not been created"
        wf_service = netsvc.LocalService('workflow')
        event = 'openerp.addons.connector_ecommerce.invoice.on_invoice_validated'
        with mock.patch(event) as event_mock:
            wf_service.trg_validate(uid, 'account.invoice',
                                    self.invoice.id, 'invoice_open', cr)
            self.assertEqual(self.invoice.state, 'open')
            event_mock.fire.assert_called_with(mock.ANY,
                                               'account.invoice',
                                               self.invoice.id)

    def test_event_paid(self):
        """ Test if the ``on_invoice_paid`` event is fired
        when an invoice is paid """
        cr, uid = self.cr, self.uid
        assert self.invoice, "The invoice has not been created"
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(uid, 'account.invoice',
                                self.invoice.id, 'invoice_open', cr)
        self.assertEqual(self.invoice.state, 'open')
        journal_id = self.get_ref('account', 'bank_journal')[1]
        pay_account_id = self.get_ref('account', 'cash')[1]
        period_id = self.get_ref('account', 'period_10')[1]
        event = 'openerp.addons.connector_ecommerce.invoice.on_invoice_paid'
        with mock.patch(event) as event_mock:
            self.invoice.pay_and_reconcile(
                pay_amount=self.invoice.amount_total,
                pay_account_id=pay_account_id,
                period_id=period_id,
                pay_journal_id=journal_id,
                writeoff_acc_id=pay_account_id,
                writeoff_period_id=period_id,
                writeoff_journal_id=journal_id,
                name="Payment for test of the event on_invoice_paid")
            self.invoice.refresh()
            self.assertEqual(self.invoice.state, 'paid')
            event_mock.fire.assert_called_with(mock.ANY,
                                               'account.invoice',
                                               self.invoice.id)
