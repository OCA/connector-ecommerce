# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Joel Grand-Guillaume
#    Copyright 2013-2015 Camptocamp SA
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
    def action_done(self):
        res = super(StockPicking, self).action_done()
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)
        # Look if it exists a backorder, in that case call for partial
        for picking in self:
            if picking.picking_type_id.code != 'outgoing':
                continue
            if picking.related_backorder_ids:
                picking_method = 'partial'
            else:
                picking_method = 'complete'
            on_picking_out_done.fire(session, self._name,
                                     picking.id, picking_method)
        return res

    @api.multi
    def write(self, vals):
        res = super(StockPicking, self).write(vals)
        if vals.get('carrier_tracking_ref'):
            session = ConnectorSession(self.env.cr, self.env.uid,
                                       context=self.env.context)
            for record_id in self.ids:
                on_tracking_number_added.fire(session, self._name, record_id)
        return res
