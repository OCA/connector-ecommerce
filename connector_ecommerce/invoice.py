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

from openerp.osv import fields, orm, osv
from openerp.tools.translate import _
from openerp.addons.connector.session import ConnectorSession
from .event import on_invoice_paid, on_invoice_validated


class account_invoice(orm.Model):
    _inherit='account.invoice'

    _columns = {
        'sale_order_ids': fields.many2many(  # TODO duplicate with 'sale_ids', replace
            'sale.order',
            'sale_order_invoice_rel',
            'invoice_id',
            'order_id',
            string='Sale Orders', readonly=True,
            help="This is the list of sale orders related to this invoice."),
    }

    def confirm_paid(self, cr, uid, ids, context=None):
        res = super(account_invoice, self).confirm_paid(
                cr, uid, ids, context=context)
        session = ConnectorSession(cr, uid, context=context)
        for record_id in ids:
            on_invoice_paid.fire(session, self._name, record_id)
        return res

    def invoice_validate(self, cr, uid, ids, context=None):
        res = super(account_invoice, self).invoice_validate(
                cr, uid, ids, context=context)
        session = ConnectorSession(cr, uid, context=context)
        for record_id in ids:
            on_invoice_validated.fire(session, self._name, record_id)
        return res
