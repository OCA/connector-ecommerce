# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
#   connector_ecommerce for OpenERP                                       #
#   Copyright (C) 2011 Akretion Sébastien BEAU <sebastien.beau@akretion.com>  #
#                                                                             #
#   This program is free software: you can redistribute it and/or modify      #
#   it under the terms of the GNU Affero General Public License as            #
#   published by the Free Software Foundation, either version 3 of the        #
#   License, or (at your option) any later version.                           #
#                                                                             #
#   This program is distributed in the hope that it will be useful,           #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
#   GNU Affero General Public License for more details.                       #
#                                                                             #
#   You should have received a copy of the GNU Affero General Public License  #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.     #
#                                                                             #
###############################################################################
from openerp.osv.orm import Model
from openerp.osv import fields
from openerp.addons.connector.session import ConnectorSession
from .event import on_invoice_validated, on_invoice_paid

class account_invoice(Model):
    _inherit='account.invoice'
    
    _columns = {
        'sale_order_ids': fields.many2many('sale.order', 'sale_order_invoice_rel', 
            'invoice_id', 'order_id', 'Sale Orders', readonly=True, 
            help="This is the list of sale orders related to this invoice."),
    }
    
    def _get_related_so_shop(self, invoice):
        """
        As several SO can be linked to several Invoice, we try to get the common
        shop between them all. The goal is further, in the consummer implementation,
        to be able to retieve the right backend to use.
        
        :param invoice is a browse record of account.invoice
        :type browse record
        :return a common sale.shop browse record between all related sale order or 
        :raise an ValueError exception if we didn't found exactly one common shop
        """
        shop = set()
        for so in invoice.sale_order_ids:
            shop.append(so.shop_id)
        if len(shop) != 1:
            raise ValueError("Wrong value for sale_order_ids, an invoice cannot"
                "be related to sale orders that doesn't belong to the same shop, "
                "but must belong to one at least (shop: %s)."%(shop))
        return shop[0]
    
    def confirm_paid(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        res = super(account_invoice, self).confirm_paid(cr, uid, ids, context)
        session = ConnectorSession(cr, uid, context=context)
        for record_id in ids:
            on_invoice_paid.fire(session, self._name, record_id)
        return res

    
    # TO REVIEW
    # _columns={
    #     'shop_id': fields.many2one('sale.shop', 'Shop', readonly=True, states={'draft': [('readonly', False)]}),
    #     'do_not_export': fields.boolean(
    #         'Do not export',
    #          help="This delivery order will not be exported "
    #               "to the external referential."),
    # }
    # 
    # def _prepare_invoice_refund(self, cr, uid, ids, invoice_vals, date=None, period_id=None, description=None, journal_id=None, context=None):
    #     invoice = self.browse(cr, uid, invoice_vals['id'], context=context)
    #     invoice_vals = super(account_invoice, self)._prepare_invoice_refund(cr, uid, ids, invoice_vals, date=date, period_id=period_id, 
    #                                                 description=description, journal_id=journal_id, context=context)
    #     invoice_vals.update({
    #             'sale_ids': [(6,0, [sale.id for sale in invoice.sale_ids])],
    #             'shop_id': invoice.shop_id.id,
    #         })
    #     return invoice_vals
