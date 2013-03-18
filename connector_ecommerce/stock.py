# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Joel Grand-Guillaume
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

from openerp.osv import orm, fields

from openerp.addons.connector.session import ConnectorSession
from .event import on_picking_out_done, on_tracking_number_added

class stock_picking(orm.Model):
    _inherit = 'stock.picking'

    _columns = {
        'related_backorder_ids': fields.one2many(
            'stock.picking', 'backorder_id',
            string="Related backorders"),
    }

    def action_done(self, cr, uid, ids, context=None):
        res = super(stock_picking, self).action_done(cr, uid,
                                                     ids, context=context)
        session = ConnectorSession(cr, uid, context=context)
        # Look if it exists a backorder, in that case call for partial
        picking_records = self.read(cr, uid, ids,
                                 ['id', 'related_backorder_ids', 'type'],
                                 context=context)
        for picking_vals in picking_records:
            if picking_vals['type'] != 'out':
                continue
            if picking_vals['related_backorder_ids']:
                picking_method = 'partial'
            else:
                picking_method = 'complete'
            on_picking_out_done.fire(session, self._name,
                                     picking_vals['id'], picking_method)
        return res


class stock_picking_out(orm.Model):
    _inherit = 'stock.picking.out'

    def write(self, cr, uid, ids, vals, context=None):
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        res = super(stock_picking_out, self).write(cr, uid, ids,
                                                   vals, context=context)
        if vals.get('carrier_tracking_ref'):
            session = ConnectorSession(cr, uid, context=context)
            for record_id in ids:
                on_tracking_number_added.fire(session, self._name, record_id)
        return res
