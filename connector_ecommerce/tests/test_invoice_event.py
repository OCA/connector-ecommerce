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

# from openerp.addons.connector_ecommerce.event import (on_invoice_paid,
#                                                       on_invoice_validated)
from openerp.addons.connector.session import ConnectorSession
import openerp.tests.common as common
from openerp import netsvc

DB = common.DB
ADMIN_USER_ID = common.ADMIN_USER_ID


class test_invoice_event(common.TransactionCase):
    """ Test if the events on the invoice are fired correctly """

    def setUp(self):
        super(test_invoice_event, self).setUp()
        cr, uid = self.cr, self.uid
        self.invoice_model = self.registry('account.invoice')
        partner_model = self.registry('res.partner')
        partner_id = partner_model.create(cr, uid, {'name': 'Hodor'})
        data_model = self.registry('ir.model.data')
        product_id = data_model.get_object_reference(cr, uid,
                                                     'product',
                                                     'product_product_6')[1]
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
        path = 'openerp.addons.connector_ecommerce.invoice.on_invoice_validated'
        with mock.patch(path) as EventMock:
            wf_service.trg_validate(uid, 'account.invoice',
                                    self.invoice.id, 'invoice_open', cr)
            EventMock.fire.assert_called_with(mock.ANY,
                                              'account.invoice',
                                              self.invoice.id)
