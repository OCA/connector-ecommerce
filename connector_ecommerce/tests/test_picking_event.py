# -*- coding: utf-8 -*-
# © 2015-2016 Camptocamp SA
# © 2018 FactorLibre
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import mock

import odoo.tests.common as common


class TestPickingEvent(common.TransactionCase):
    """ Test if the events on the pickings are fired correctly """

    def _create_pack_operation(self, product, product_qty, picking_id,
                               **values):
        move_line_env = self.env['stock.move.line']
        vals = {
            'picking_id': picking_id.id,
            'product_id': product.id,
            'product_qty': product_qty,
            'qty_done': product_qty}
        vals.update(**values)
        pack_operation = move_line_env.new(vals)
        pack_operation.onchange_product_id()
        return move_line_env.create(
            pack_operation._convert_to_write(pack_operation._cache))

    def setUp(self):
        super(TestPickingEvent, self).setUp()
        self.picking_model = self.env['stock.picking']
        self.sale_model = self.env['sale.order']
        self.sale_line_model = self.env['sale.order.line']

        partner_model = self.env['res.partner']
        partner = partner_model.create({'name': 'Benjy'})
        self.product_6 = self.env.ref('product.product_product_6')
        self.product_7 = self.env.ref('product.product_product_7')
        self.sale = self.sale_model.create({'partner_id': partner.id})
        self.sale_line_model.create({
            'order_id': self.sale.id,
            'product_id': self.product_6.id,
            'name': "iPad Mini",
            'product_uom_qty': 42,
            'product_uom': self.env.ref('uom.product_uom_unit').id,
            'price_unit': 65,
        })
        self.sale_line_model.create({
            'order_id': self.sale.id,
            'product_id': self.product_7.id,
            'name': "Apple In-Ear Headphones",
            'product_uom_qty': 2,
            'product_uom': self.env.ref('uom.product_uom_unit').id,
            'price_unit': 405,
        })
        self.sale.action_confirm()
        self.picking = self.sale.picking_ids
        self.location_id = self.picking.move_lines[0].location_id.id
        self.location_dest_id = self.picking.move_lines[0].location_dest_id.id

    def test_event_on_picking_out_done(self):
        """ Test if the ``on_picking_out_done`` event is fired
        when an outgoing picking is done """
        mock_method = 'odoo.addons.component_event.models.base.Base._event'
        with mock.patch(mock_method) as mock_event:
            self._create_pack_operation(
                self.product_6, 42, self.picking,
                location_id=self.location_id,
                location_dest_id=self.location_dest_id)
            self._create_pack_operation(
                self.product_7, 2, self.picking,
                location_id=self.location_id,
                location_dest_id=self.location_dest_id)
            self.picking.action_done()
            self.assertEqual(self.picking.state, 'done')
            mock_event('on_picking_out_done').notify.assert_called_with(
                self.picking, 'complete')

    def test_event_on_picking_out_done_partial(self):
        """ Test if the ``on_picking_out_done`` informs of the partial
        pickings """
        mock_method = 'odoo.addons.component_event.models.base.Base._event'
        with mock.patch(mock_method) as mock_event:
            self._create_pack_operation(
                self.product_6, 1, self.picking,
                location_id=self.location_id,
                location_dest_id=self.location_dest_id)
            self._create_pack_operation(
                self.product_7, 1, self.picking,
                location_id=self.location_id,
                location_dest_id=self.location_dest_id)
            self.picking.action_done()
            self.assertEqual(self.picking.state, 'done')
            mock_event('on_picking_out_done').notify.assert_called_with(
                self.picking, 'partial')

    def test_event_on_tracking_number_added(self):
        """ Test if the ``on_tracking_number_added`` event is fired
        when a tracking number is added """
        mock_method = 'odoo.addons.component_event.models.base.Base._event'
        with mock.patch(mock_method) as mock_event:
            self.picking.carrier_tracking_ref = 'XYZ'
            mock_event('on_tracking_number_added').notify.assert_called_with(
                self.picking)
