# -*- coding: utf-8 -*-
# © 2018 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import mock

import odoo.tests.common as common


class TestProductEvent(common.TransactionCase):
    """ Test if the events on the products are fired correctly """

    def setUp(self):
        super(TestProductEvent, self).setUp()
        self.product_product = self.env.ref('product.product_product_6')
        self.product_template = self.env.ref(
                'product.product_product_11_product_template')

    def test_event_on_product_product_price_changed(self):
        """ Test if the ``on_product_price_changed`` event is fired
        when a product product price is changed"""
        event = ('odoo.addons.connector_ecommerce.models.'
                 'product.on_product_price_changed')
        with mock.patch(event) as event_mock:
            self.product_product.update({'lst_price': 1000.0})
            self.assertEquals(self.product_product.lst_price, 1000.0)
            event_mock.fire.assert_called_with(mock.ANY,
                                               'product.product',
                                               self.product_product.id)

    def test_event_on_product_template_price_changed(self):
        """ Test if the ``on_product_price_changed`` event is fired
        when a product template price is changed"""
        event = ('odoo.addons.connector_ecommerce.models.'
                 'product.on_product_price_changed')
        with mock.patch(event) as event_mock:
            self.product_template.update({'list_price': 1000.0})
            self.assertEquals(self.product_template.list_price, 1000.0)
            self.assertEquals(event_mock.fire.call_count, 2)
            event_mock.fire.assert_called_with(mock.ANY,
                                               'product.product',
                                               mock.ANY)
