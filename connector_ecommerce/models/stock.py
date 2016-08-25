# -*- coding: utf-8 -*-
# © 2013-2015 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp import models, fields, api

from openerp.addons.connector.session import ConnectorSession
from .event import on_picking_out_done, on_tracking_number_added


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    related_backorder_ids = fields.One2many(
        comodel_name='stock.picking',
        inverse_name='backorder_id',
        string="Related backorders",
    )

    @api.multi
    def write(self, vals):
        res = super(StockPicking, self).write(vals)
        if vals.get('carrier_tracking_ref'):
            session = ConnectorSession.from_env(self.env)
            for record_id in self.ids:
                on_tracking_number_added.fire(session, self._name, record_id)
        return res

    @api.multi
    def do_transfer(self):
        # The key in the context avoid the event to be fired in
        # StockMove.action_done(). Allow to handle the partial pickings
        self_context = self.with_context(__no_on_event_out_done=True)
        result = super(StockPicking, self_context).do_transfer()
        session = ConnectorSession.from_env(self.env)
        for picking in self:
            if picking.picking_type_id.code != 'outgoing':
                continue
            if picking.related_backorder_ids:
                method = 'partial'
            else:
                method = 'complete'
            on_picking_out_done.fire(session, 'stock.picking',
                                     picking.id, method)

        return result


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def action_done(self):
        fire_event = not self.env.context.get('__no_on_event_out_done')
        if fire_event:
            pickings = self.mapped('picking_id')
            states = {p.id: p.state for p in pickings}

        result = super(StockMove, self).action_done()

        if fire_event:
            session = ConnectorSession.from_env(self.env)
            for picking in pickings:
                if states[picking.id] != 'done' and picking.state == 'done':
                    if picking.picking_type_id.code != 'outgoing':
                        continue
                    # partial pickings are handled in
                    # StockPicking.do_transfer()
                    on_picking_out_done.fire(session, 'stock.picking',
                                             picking.id, 'complete')

        return result
