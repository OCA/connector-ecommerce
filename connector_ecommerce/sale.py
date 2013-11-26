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

import logging

from openerp.osv import orm, fields, osv
from openerp.tools.translate import _
from openerp import netsvc
from openerp.addons.connector.connector import ConnectorUnit

_logger = logging.getLogger(__name__)


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
    """ Add a cancellation mecanism in the sales orders

    When a sale order is canceled in a backend, the connectors can flag
    the 'canceled_in_backend' flag. It will:

    * try to automatically cancel the sales order
    * block the confirmation of the sales orders using a 'sales exception'

    When a sales order is canceled or the user used the button to force
    to 'keep it open', the flag 'cancellation_resolved' is set to True.

    The second axe which can be used by the connectors is the 'parent'
    sale order. When a sales order has a parent sales order (logic to
    link with the parent to be defined by each connector), it will be
    blocked until the cancellation of the sale order is resolved.

    This is used by, for instance, the magento connector, when one
    modifies a sales order, Magento cancels it and create a new one with
    the first one as parent.
    """
    _inherit = 'sale.order'

    def _get_parent_id(self, cr, uid, ids, name, arg, context=None):
        return self.get_parent_id(cr, uid, ids, context=context)

    def get_parent_id(self, cr, uid, ids, context=None):
        """ Need to be inherited in the connectors to implement the
        parent logic.

        See an implementation example in ``magentoerpconnect``.
        """
        return dict.fromkeys(ids, False)

    def _get_need_cancel(self, cr, uid, ids, name, arg, context=None):
        result = {}
        for order in self.browse(cr, uid, ids, context=context):
            result[order.id] = self._need_cancel(cr, uid, order,
                                                 context=context)
        return result

    def _get_parent_need_cancel(self, cr, uid, ids, name, arg, context=None):
        result = {}
        for order in self.browse(cr, uid, ids, context=context):
            result[order.id] = self._parent_need_cancel(cr, uid, order,
                                                        context=context)
        return result

    _columns = {
        'canceled_in_backend': fields.boolean('Canceled in backend',
                                               readonly=True),
        # set to True when the cancellation from the backend is
        # resolved, either because the SO has been canceled or
        # because the user manually chosed to keep it open
        'cancellation_resolved': fields.boolean('Cancellation from the '
                                                'backend resolved'),
        'parent_id': fields.function(_get_parent_id,
                                     string='Parent Order',
                                     type='many2one',
                                     help='A parent sales order is a sales '
                                          'order replaced by this one.',
                                     relation='sale.order'),
        'need_cancel': fields.function(_get_need_cancel,
                                       string='Need to be canceled',
                                       type='boolean',
                                       help='Has been canceled on the backend'
                                            ', need to be canceled.'),
        'parent_need_cancel': fields.function(
            _get_parent_need_cancel,
            string='A parent sales orders needs cancel',
            type='boolean',
            help='A parent sales orders has been canceled on the backend'
                 ' and needs to be canceled.'),
    }

    def _need_cancel(self, cr, uid, order, context=None):
        """ Return True if the sales order need to be canceled
        (has been canceled on the Backend) """
        return order.canceled_in_backend and not order.cancellation_resolved

    def _parent_need_cancel(self, cr, uid, order, context=None):
        """ Return True if at least one parent sales order need to
        be canceled (has been canceled on the backend).
        Follows all the parent sales orders.
        """
        def need_cancel(order):
            if self._need_cancel(cr, uid, order, context=context):
                return True
            if order.parent_id:
                return need_cancel(order.parent_id)
            else:
                return False
        if not order.parent_id:
            return False
        return need_cancel(order.parent_id)

    def _try_auto_cancel(self, cr, uid, ids, context=None):
        """ Try to automatically cancel a sales order canceled
        in a backend.

        If it can't cancel it, does nothing.
        """
        wkf_states = ('draft', 'sent')
        action_states = ('manual', 'progress')
        wf_service = netsvc.LocalService("workflow")
        resolution_msg = _("<p>Resolution:<ol>"
                           "<li>Cancel the linked invoices, delivery "
                           "orders, automatic payments.</li>"
                           "<li>Cancel the sales order manually.</li>"
                           "</ol></p>")
        for order_id in ids:
            state = self.read(cr, uid, order_id,
                              ['state'], context=context)['state']
            if state == 'cancel':
                continue
            elif state == 'done':
                message = _("The sales order cannot be automatically "
                            "canceled because it is already done.")
            elif state in wkf_states + action_states:
                try:
                    # respect the same cancellation methods than
                    # the sales order view: quotations use the workflow
                    # action, sales orders use the action_cancel method.
                    if state in wkf_states:
                        wf_service.trg_validate(uid, 'sale.order',
                                                order_id, 'cancel', cr)
                    elif state in action_states:
                        self.action_cancel(cr, uid, order_id, context=context)
                    else:
                        raise ValueError('%s should not fall here.' % state)
                except osv.except_osv:
                    # the 'cancellation_resolved' flag will stay to False
                    message = _("The sales order could not be automatically "
                                "canceled.") + resolution_msg
                else:
                    message = _("The sales order has been automatically "
                                "canceled.")
            else:
                # shipping_except, invoice_except, ...
                # can not be canceled from the view, so assume that it
                # should not be canceled here neiter, exception to
                # resolve
                message = _("The sales order could not be automatically "
                            "canceled for this status.") + resolution_msg
            self.message_post(cr, uid, [order_id], body=message,
                              context=context)

    def _log_canceled_in_backend(self, cr, uid, ids, context=None):
        message = _("The sales order has been canceled on the backend.")
        self.message_post(cr, uid, ids, body=message, context=context)
        for order in self.browse(cr, uid, ids, context=context):
            message = _("Warning: the origin sales order %s has been canceled "
                        "on the backend.") % order.name
            if order.picking_ids:
                picking_obj = self.pool.get('stock.picking')
                picking_obj.message_post(cr, uid, order.picking_ids,
                                         body=message, context=context)
            if order.invoice_ids:
                picking_obj = self.pool.get('account.invoice')
                picking_obj.message_post(cr, uid, order.invoice_ids,
                                         body=message, context=context)

    def create(self, cr, uid, values, context=None):
        order_id = super(sale_order, self).create(cr, uid, values,
                                                  context=context)
        if values.get('canceled_in_backend'):
            self._log_canceled_in_backend(cr, uid, [order_id], context=context)
            self._try_auto_cancel(cr, uid, [order_id], context=context)
        return order_id

    def write(self, cr, uid, ids, values, context=None):
        result = super(sale_order, self).write(cr, uid, ids, values,
                                               context=context)
        if values.get('canceled_in_backend'):
            self._log_canceled_in_backend(cr, uid, ids, context=context)
            self._try_auto_cancel(cr, uid, ids, context=context)
        return result

    def action_cancel(self, cr, uid, ids, context=None):
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        super(sale_order, self).action_cancel(cr, uid, ids, context=context)
        sales = self.read(cr, uid, ids,
                          ['canceled_in_backend',
                           'cancellation_resolved'],
                          context=context)
        for sale in sales:
            # the sale order is canceled => considered as resolved
            if (sale['canceled_in_backend'] and
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

    def action_view_parent(self, cr, uid, ids, context=None):
        """ Return an action to display the parent sale order """
        if isinstance(ids, (list, tuple)):
            assert len(ids) == 1
            ids = ids[0]

        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        parent = self.browse(cr, uid, ids, context=context).parent_id
        if not parent:
            return

        view_xmlid = ('sale', 'view_order_form')
        if parent.state in ('draft', 'sent', 'cancel'):
            action_xmlid = ('sale', 'action_quotations')
        else:
            action_xmlid = ('sale', 'action_orders')

        ref = mod_obj.get_object_reference(cr, uid, *action_xmlid)
        action_id = False
        if ref:
            __, action_id = ref
        action = act_obj.read(cr, uid, [action_id], context=context)[0]

        ref = mod_obj.get_object_reference(cr, uid, *view_xmlid)
        action['views'] = [(ref[1] if ref else False, 'form')]
        action['res_id'] = parent.id
        return action

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
        _logger.warning('sale_order._convert_special_fields() has been '
                        'deprecated. Use a specialized '
                        'SpecialOrderLineBuilder class instead.')
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

    def _get_order_extra_line_vals(self, cr, uid, vals, option, product,
                                   price_unit, context=None):
        return {
            'product_id': product.id,
            'name': product.name,
            'product_uom': product.uom_id.id,
            'product_uom_qty': 1,
            'price_unit': price_unit
        }

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
            return self._clean_special_fields(option, vals)
        model_data_obj = self.pool.get('ir.model.data')
        product_obj = self.pool.get('product.product')
        __, product_id = model_data_obj.get_object_reference(
            cr, uid, *option['product_ref'])
        product = product_obj.browse(cr, uid, product_id, context=context)

        extra_line = self._get_order_extra_line_vals(
            cr, uid, vals, option, product, price_unit, context=context)

        ext_code_field = option.get('code_field')
        if ext_code_field and vals.get(ext_code_field):
            extra_line['name'] = "%s [%s]" % (extra_line['name'],
                                              vals[ext_code_field])
        vals['order_line'].append((0, 0, extra_line))
        return self._clean_special_fields(option, vals)

    def _clean_special_fields(self, option, vals):
        for key in ['price_unit_tax_excluded',
                    'price_unit_tax_included',
                    'tax_rate_field']:
            if option.get(key) and option[key] in vals:
                del vals[option[key]]
        return vals  # if there is no price, we have nothing to import


class SpecialOrderLineBuilder(ConnectorUnit):
    """ Base class to build a sale order line for a sale order

    Used when extra order lines have to be added in a sale order
    but we only know some parameters (product, price, ...), for instance,
    a line for the shipping costs or the gift coupons.

    It can be subclassed to customize the way the lines are created.

    Usage::

        builder = self.get_connector_for_unit(ShippingLineBuilder,
                                              model='sale.order.line')
        builder.price_unit = 100
        builder.get_line()

    """
    _model_name = None

    def __init__(self, environment):
        super(SpecialOrderLineBuilder, self).__init__(environment)
        self.product = None  # id or browse_record
        # when no product_id, fallback to a product_ref
        self.product_ref = None  # tuple (module, xmlid)
        self.price_unit = None
        self.quantity = 1
        self.sign = 1

    def get_line(self):
        assert self.product_ref or self.product
        assert self.price_unit is not None
        line = {}
        session = self.session

        product = product_id = self.product
        if product_id is None:
            model_data_obj = session.pool.get('ir.model.data')
            __, product_id = model_data_obj.get_object_reference(
                session.cr, session.uid, *self.product_ref)

        if not isinstance(product_id, orm.browse_record):
            product = session.browse('product.product', product_id)
        return {'product_id': product.id,
                'name': product.name,
                'product_uom': product.uom_id.id,
                'product_uom_qty': self.quantity,
                'price_unit': self.price_unit * self.sign}


class ShippingLineBuilder(SpecialOrderLineBuilder):
    """ Return values for a Shipping line """
    _model_name = None

    def __init__(self, environment):
        super(ShippingLineBuilder, self).__init__(environment)
        self.product_ref = ('connector_ecommerce', 'product_product_shipping')


class CashOnDeliveryLineBuilder(SpecialOrderLineBuilder):
    """ Return values for a Cash on Delivery line """
    _model_name = None
    _model_name = None

    def __init__(self, environment):
        super(CashOnDeliveryLineBuilder, self).__init__(environment)
        self.product_ref = ('connector_ecommerce',
                            'product_product_cash_on_delivery')


class GiftOrderLineBuilder(SpecialOrderLineBuilder):
    """ Return values for a Gift line """
    _model_name = None

    def __init__(self, environment):
        super(GiftOrderLineBuilder, self).__init__(environment)
        self.product_ref = ('connector_ecommerce',
                            'product_product_gift')
        self.sign = -1
        self.gift_code = None

    def get_line(self):
        line = super(GiftOrderLineBuilder, self).get_line()
        if self.gift_code:
            line['name'] = "%s [%s]" % (line['name'], self.gift_code)
        return line
