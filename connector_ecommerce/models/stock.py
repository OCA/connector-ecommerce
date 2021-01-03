# © 2013-2015 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    related_backorder_ids = fields.One2many(
        comodel_name="stock.picking",
        inverse_name="backorder_id",
        string="Related backorders",
    )

    def write(self, vals):
        res = super(StockPicking, self).write(vals)
        if vals.get("carrier_tracking_ref"):
            for record in self:
                self._event("on_tracking_number_added").notify(record)
        return res

    def _action_done(self):
        # The key in the context avoid the event to be fired in
        # StockMove.action_done(). Allow to handle the partial pickings
        self_context = self.with_context(__no_on_event_out_done=True)
        result = super(StockPicking, self_context)._action_done()
        for picking in self:
            method = "partial" if picking.related_backorder_ids else "complete"
            if picking.picking_type_id.code == "outgoing":
                self._event("on_picking_out_done").notify(picking, method)
            elif (
                picking.picking_type_id.code == "incoming"
                and picking.location_dest_id.usage == "customer"
            ):
                self._event("on_picking_dropship_done").notify(picking, method)

        return result


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_done(self, cancel_backorder=False):
        fire_event = not self.env.context.get("__no_on_event_out_done")
        if fire_event:
            pickings = self.mapped("picking_id")
            states = {p.id: p.state for p in pickings}

        result = super()._action_done(cancel_backorder=cancel_backorder)

        if fire_event:
            for picking in pickings:
                if states[picking.id] != "done" and picking.state == "done":
                    if picking.picking_type_id.code != "outgoing":
                        continue
                    # partial pickings are handled in
                    # StockPicking.do_transfer()
                    picking._event("on_picking_out_done").notify(picking, "complete")

        return result
