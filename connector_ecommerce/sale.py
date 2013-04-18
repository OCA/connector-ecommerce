# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2011-2013 Camptocamp SA
#    Author: Sébastien Beau
#    Copyright 2010-2013 Akretion
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
from openerp.tools.translate import _


class sale_shop(orm.Model):
    _inherit = 'sale.shop'

    def _get_payment_default(self, cr, uid, context=None):
        """ Return a arbitrary account.payment.term record for the sale.shop

        ``sale.shop`` records are created dynamically from the backends
        and the field ``payment_default_id`` needs a default value.
        """
        data_obj = self.pool.get('ir.model.data')
        __, payment_id = data_obj.get_object_reference(
                cr, uid, 'account', 'account_payment_term_immediate')
        return payment_id

    _defaults = {
        # see method docstring for explanation
        'payment_default_id': _get_payment_default,
    }


class sale_order(orm.Model):
    _inherit = 'sale.order'

    def _get_parent_id(self, cr, uid, ids, name, arg, context=None):
        return self.pool.get('sale.order').get_parent_id(cr, uid, ids,
                                                         context=context)

    def get_parent_id(self, cr, uid, ids, context=None):
        """ Need to be inherited in the connectors to implement the
        parent logic.

        See an implementation example in ``magentoerpconnect``.
        """
        return dict.fromkeys(ids, False)

    _columns = {
        'cancelled_in_backend': fields.boolean('Cancelled in backend',
                                               readonly=True),
        # set to True when the cancellation from the backend is
        # resolved, either because the SO has been canceled or
        # because the user manually chosed to keep it open
        'cancellation_resolved': fields.boolean('Cancellation from the '
                                                'backend resolved'),
        'parent_id': fields.function(_get_parent_id,
                                     string='Parent Order',
                                     type='many2one',
                                     relation='sale.order'),
    }

    def _log_cancelled_in_backend(self, cr, uid, ids, context=None):
        message = _("The sales order has been cancelled on the backend.")
        self.message_post(cr, uid, ids, body=message, context=context)

    def create(self, cr, uid, values, context=None):
        order_id = super(sale_order, self).create(cr, uid, values,
                                                  context=context)
        if values.get('cancelled_in_backend'):
            self._log_cancelled_in_backend(cr, uid, [order_id],
                                           context=context)
        return order_id

    def write(self, cr, uid, ids, values, context=None):
        if values.get('cancelled_in_backend'):
            self._log_cancelled_in_backend(cr, uid, ids, context=context)
        return super(sale_order, self).write(cr, uid, ids, values,
                                             context=context)

    def action_cancel(self, cr, uid, ids, context=None):
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        super(sale_order, self).action_cancel(cr, uid, ids, context=context)
        sales = self.read(cr, uid, ids,
                          ['cancelled_in_backend',
                           'cancellation_resolved'],
                          context=context)
        for sale in sales:
            # the sale order is cancelled => considered as resolved
            if (sale['cancelled_in_backend'] and
                    not sale['cancellation_resolved']):
                self.write(cr, uid, sale['id'],
                           {'cancellation_resolved': True},
                           context=context)
        return True

    def ignore_cancellation(self, cr, uid, ids, reason, context=None):
        """ Manually set the cancellation from the backend as resolved.

        The user can choose to keep the sale order active for some reason,
        so it just push a button to keep it alive.
        """
        message = (_("Despite the cancellation of the sales order on the "
                     "backend, it should stay open.<br/><br/>Reason: %s") %
                   reason)
        self.message_post(cr, uid, ids, body=message, context=context)
        self.write(cr, uid, ids,
                   {'cancellation_resolved': True},
                   context=context)
        return True

    # XXX the 3 next methods seems very specific to magento
    def _convert_special_fields(self, cr, uid, vals, order_lines, context=None):
        """ Convert the special 'fake' field into an order line.

        Special fields are:
        - shipping amount and shipping_tax_rate
        - cash_on_delivery and cash_on_delivery_taxe_rate
        - gift_certificates

        :param vals: values of the sale order to create
        :type vals: dict
        :param order_lines: lines of the orders to import
        :return: the value for the sale order with the special field converted
        :rtype: dict
        """
        shipping_fields = ['shipping_amount_tax_excluded',
                           'shipping_amount_tax_included',
                           'shipping_tax_amount']

        def check_key(keys):
            return len(set(shipping_fields) & set(keys)) >= 2

        vals.setdefault('order_line', [])
        for line in order_lines:
            for field in shipping_fields:
                if field in line[2]:
                    vals[field] = vals.get(field, 0.0) + line[2][field]
                    del line[2][field]

        if not 'shipping_tax_rate' in vals and check_key(vals.keys()):
            if not 'shipping_amount_tax_excluded' in vals:
                vals['shipping_amount_tax_excluded'] = vals['shipping_amount_tax_included'] - vals['shipping_tax_amount']
            elif not 'shipping_tax_amount' in vals:
                vals['shipping_tax_amount'] = vals['shipping_amount_tax_included'] - vals['shipping_amount_tax_excluded']
            if vals['shipping_amount_tax_excluded']:
                vals['shipping_tax_rate'] = vals['shipping_tax_amount'] / vals['shipping_amount_tax_excluded']
            else:
                vals['shipping_tax_rate'] = 0.
            del vals['shipping_tax_amount']
        for option in self._get_special_fields(cr, uid, context=context):
            vals = self._add_order_extra_line(cr, uid, vals,
                                              option, context=context)
        return vals

    def _get_special_fields(self, cr, uid, context=None):
        return [
            {
            'price_unit_tax_excluded': 'shipping_amount_tax_excluded',
            'price_unit_tax_included': 'shipping_amount_tax_included',
            'tax_rate_field': 'shipping_tax_rate',
            'product_ref': ('connector_ecommerce', 'product_product_shipping'),
            },
            {
            'tax_rate_field': 'cash_on_delivery_taxe_rate',
            'price_unit_tax_excluded': 'cash_on_delivery_amount_tax_excluded',
            'price_unit_tax_included': 'cash_on_delivery_amount_tax_included',
            'product_ref': ('connector_ecommerce', 'product_product_cash_on_delivery'),
            },
            {
            #gift certificate doesn't have any tax
            'price_unit_tax_excluded': 'gift_certificates_amount',
            'price_unit_tax_included': 'gift_certificates_amount',
            'product_ref': ('connector_ecommerce', 'product_product_gift'),
            'code_field': 'gift_certificates_code',
            'sign': -1,
            },
        ]

    def _add_order_extra_line(self, cr, uid, vals, option, context=None):
        """ Add or substract amount on order as a separate line item
        with single quantity for each type of amounts like: shipping,
        cash on delivery, discount, gift certificates...

        :param dict vals: values of the sale order to create
        :param option: dictionary of options for the special field to process
        """
        if context is None:
            context = {}
        sign = option.get('sign', 1)
        if (context.get('is_tax_included') and
                vals.get(option['price_unit_tax_included'])):
            price_unit = vals.pop(option['price_unit_tax_included']) * sign
        elif vals.get(option['price_unit_tax_excluded']):
            price_unit = vals.pop(option['price_unit_tax_excluded']) * sign
        else:
            for key in ['price_unit_tax_excluded',
                        'price_unit_tax_included',
                        'tax_rate_field']:
                if option.get(key) and option[key] in vals:
                    del vals[option[key]]
            return vals  # if there is no price, we have nothing to import

        model_data_obj = self.pool.get('ir.model.data')
        product_obj = self.pool.get('product.product')
        __, product_id = model_data_obj.get_object_reference(
                cr, uid, *option['product_ref'])
        product = product_obj.browse(cr, uid, product_id, context=context)

        extra_line = {'product_id': product.id,
                      'name': product.name,
                      'product_uom': product.uom_id.id,
                      'product_uom_qty': 1,
                      'price_unit': price_unit}

        ext_code_field = option.get('code_field')
        if ext_code_field and vals.get(ext_code_field):
            extra_line['name'] = "%s [%s]" % (extra_line['name'],
                                              vals[ext_code_field])
        vals['order_line'].append((0, 0, extra_line))
        return vals
