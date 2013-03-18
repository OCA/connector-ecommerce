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

from openerp.osv import orm, fields


class sale_ignore_cancel(orm.TransientModel):
    _name = 'sale.ignore.cancel'
    _description = 'Ignore Sales Order Cancel'

    _columns = {
        'reason': fields.html('Reason', required=True),
    }

    def confirm_ignore_cancel(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (list, tuple)):
            assert len(ids) == 1
            ids = ids[0]
        order_ids = context.get('active_ids')
        if order_ids is None:
            return
        form = self.browse(cr, uid, ids, context=context)
        self.pool.get('sale.order').ignore_cancellation(cr, uid, order_ids,
                                                        form.reason,
                                                        context=context)
        return {'type': 'ir.actions.act_window_close'}
