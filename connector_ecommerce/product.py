# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Sébastien BEAU
#    Copyright 2011-2013 Akretion
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
from .event import on_product_price_changed


class product_template(orm.Model):
    _inherit = 'product.template'

    #TODO implement set function and also support multi tax
    def _get_tax_group_id(self, cr, uid, ids, field_name, args, context=None):
        result = {}
        for product in self.browse(cr, uid, ids, context=context):
            taxes = product.taxes_id
            result[product.id] = taxes[0].group_id.id if taxes else False
        return result

    _columns = {
        'tax_group_id': fields.function(
                            _get_tax_group_id,
                            string='Tax Group',
                            type='many2one',
                            relation='account.tax.group',
                            store=False,
                            help='Tax group are used with some external '
                                 'system like magento or prestashop'),
    }

    def _price_changed(self, cr, uid, ids, vals, context=None):
        """ Fire the ``on_product_price_changed`` on all the variants of
        the template if the price if the product could have changed.

        If one of the field used in a sale pricelist item has been
        modified, we consider that the price could have changed.

        There is no guarantee that's the price actually changed,
        because it depends on the pricelists.
        """
        if context is None:
            context = {}
        type_obj = self.pool['product.price.type']
        price_fields = type_obj.sale_price_fields(cr, uid, context=context)
        # restrict the fields to the template ones only, so if
        # the write has been done on product.product, we won't
        # update all the variant if a price field of the
        # variant has been changed
        tmpl_fields = [field for field in vals if field in self._columns]
        if any(field in price_fields for field in tmpl_fields):
            product_obj = self.pool['product.product']
            session = ConnectorSession(cr, uid, context=context)
            product_ids = product_obj.search(cr, uid,
                                             [('product_tmpl_id', 'in', ids)],
                                             context=context)
            # when the write is done on the product.product, avoid
            # to fire the event 2 times
            if context.get('from_product_ids'):
                product_ids = list(set(product_ids) -
                                   set(context['from_product_ids']))
            for prod_id in product_ids:
                on_product_price_changed.fire(session,
                                              product_obj._name,
                                              prod_id)

    def write(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        result = super(product_template, self).write(cr, uid, ids,
                                                     vals, context=context)
        self._price_changed(cr, uid, ids, vals, context=context)
        return result


class product_product(orm.Model):
    _inherit = 'product.product'

    def _get_checkpoint(self, cr, uid, ids, name, arg, context=None):
        result = {}
        checkpoint_obj = self.pool.get('connector.checkpoint')
        model_obj = self.pool.get('ir.model')
        model_id = model_obj.search(cr, uid,
                                    [('model', '=', 'product.product')],
                                    context=context)[0]
        for product_id in ids:
            point_ids = checkpoint_obj.search(cr, uid,
                                              [('model_id', '=', model_id),
                                               ('record_id', '=', product_id),
                                               ('state', '=', 'need_review')],
                                              context=context)
            result[product_id] = bool(point_ids)
        return result

    _columns = {
        'has_checkpoint': fields.function(_get_checkpoint,
                                          type='boolean',
                                          readonly=True,
                                          string='Has Checkpoint'),
    }

    def _price_changed(self, cr, uid, ids, vals, context=None):
        """ Fire the ``on_product_price_changed`` if the price
        if the product could have changed.

        If one of the field used in a sale pricelist item has been
        modified, we consider that the price could have changed.

        There is no guarantee that's the price actually changed,
        because it depends on the pricelists.
        """
        type_obj = self.pool['product.price.type']
        price_fields = type_obj.sale_price_fields(cr, uid, context=context)
        if any(field in price_fields for field in vals):
            session = ConnectorSession(cr, uid, context=context)
            for prod_id in ids:
                on_product_price_changed.fire(session, self._name, prod_id)

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        context = context.copy()
        context['from_product_ids'] = ids
        result = super(product_product, self).write(
            cr, uid, ids, vals, context=context)
        self._price_changed(cr, uid, ids, vals, context=context)
        return result

    def create(self, cr, uid, vals, context=None):
        product_ids = super(product_product, self).create(
            cr, uid, vals, context=context)
        self._price_changed(cr, uid, [product_ids], vals, context=context)
        return product_ids


class product_price_type(orm.Model):
    _inherit = 'product.price.type'

    _columns = {
        'pricelist_item_ids': fields.one2many(
            'product.pricelist.item', 'base',
            string='Pricelist Items',
            readonly=True)
    }

    def sale_price_fields(self, cr, uid, context=None):
        """ Returns a list of fields used by sale pricelists.
        Used to know if the sale price could have changed
        when one of these fields has changed.
        """
        item_obj = self.pool['product.pricelist.item']
        item_ids = item_obj.search(
            cr, uid,
            [('price_version_id.pricelist_id.type', '=', 'sale')],
            context=context)
        type_ids = self.search(cr, uid,
                               [('pricelist_item_ids', 'in', item_ids)],
                               context=context)
        types = self.read(cr, uid, type_ids, ['field'], context=context)
        return [t['field'] for t in types]
