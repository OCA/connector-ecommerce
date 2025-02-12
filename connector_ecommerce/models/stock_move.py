# © 2013-2015 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


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
