# -*- coding: utf-8 -*-
# © 2015-2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import mock

import odoo.tests.common as common


class TestPickingEvent(common.TransactionCase):
    """ Test if the events on the pickings are fired correctly """

    def setUp(self):
        super(TestPickingEvent, self).setUp()
        self.picking_model = self.env['stock.picking']
        self.sale_model = self.env['sale.order']
        self.sale_line_model = self.env['sale.order.line']

        partner_model = self.env['res.partner']
        partner = partner_model.create({'name': 'Benjy'})
        self.sale = self.sale_model.create({'partner_id': partner.id})
        self.sale_line_model.create({
            'order_id': self.sale.id,
            'product_id': self.env.ref('product.product_product_6').id,
            'name': "iPad Mini",
            'product_uom_qty': 42,
            'product_uom': self.env.ref('product.product_uom_unit').id,
            'price_unit': 65,
        })
        self.sale_line_model.create({
            'order_id': self.sale.id,
            'product_id': self.env.ref('product.product_product_7').id,
            'name': "Apple In-Ear Headphones",
            'product_uom_qty': 2,
            'product_uom': self.env.ref('product.product_uom_unit').id,
            'price_unit': 405,
        })
        self.sale.action_confirm()
        self.picking = self.sale.picking_ids

    def test_event_on_picking_out_done(self):
        """ Test if the ``on_picking_out_done`` event is fired
        when an outgoing picking is done """
        self.picking.force_assign()
        event = ('odoo.addons.connector_ecommerce.models.'
                 'stock.on_picking_out_done')
        with mock.patch(event) as event_mock:
            self.picking.action_done()
            self.assertEquals(self.picking.state, 'done')
            event_mock.fire.assert_called_with(mock.ANY,
                                               'stock.picking',
                                               self.picking.id,
                                               'complete')

    def test_event_on_picking_out_done_partial(self):
        """ Test if the ``on_picking_out_done`` informs of the partial
        pickings """
        self.picking.force_assign()
        self.picking.do_prepare_partial()
        for operation in self.picking.pack_operation_ids:
            operation.product_qty = 1
        event = ('odoo.addons.connector_ecommerce.models.'
                 'stock.on_picking_out_done')
        with mock.patch(event) as event_mock:
            self.picking.do_transfer()
            self.assertEquals(self.picking.state, 'done')
            event_mock.fire.assert_called_with(mock.ANY,
                                               'stock.picking',
                                               self.picking.id,
                                               'partial')

    def test_event_on_tracking_number_added(self):
        """ Test if the ``on_tracking_number_added`` event is fired
        when a tracking number is added """
        event = ('odoo.addons.connector_ecommerce.models.'
                 'stock.on_tracking_number_added')
        with mock.patch(event) as event_mock:
            self.picking.carrier_tracking_ref = 'XYZ'
            event_mock.fire.assert_called_with(mock.ANY,
                                               'stock.picking',
                                               self.picking.id)
