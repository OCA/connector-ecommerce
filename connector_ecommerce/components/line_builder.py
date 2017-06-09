# -*- coding: utf-8 -*-
# © 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models
from odoo.addons.component.core import Component


class SpecialOrderLineBuilder(Component):
    """ Base class to build a sales order line for a sales order

    Used when extra order lines have to be added in a sales order
    but we only know some parameters (product, price, ...), for instance,
    a line for the shipping costs or the gift coupons.

    It can be subclassed to customize the way the lines are created.

    Usage::

        builder = self.components(usage='shipping.line.builder',
                                  model_name='sale.order.line')
        builder.price_unit = 100
        builder.get_line()

    """
    _name = 'ecommerce.order.line.builder'
    _inherit = 'base.connector'
    _usage = 'order.line.builder'

    def __init__(self, work_context):
        super(SpecialOrderLineBuilder, self).__init__(work_context)
        self.product = None  # id or browse_record
        # when no product_id, fallback to a product_ref
        self.product_ref = None  # tuple (module, xmlid)
        self.price_unit = None
        self.quantity = 1
        self.sign = 1
        self.sequence = 980

    def get_line(self):
        assert self.product_ref or self.product
        assert self.price_unit is not None

        product = self.product
        if product is None:
            product = self.env.ref('.'.join(self.product_ref))

        if not isinstance(product, models.BaseModel):
            product = self.env['product.product'].browse(product)
        return {'product_id': product.id,
                'name': product.name,
                'product_uom': product.uom_id.id,
                'product_uom_qty': self.quantity,
                'price_unit': self.price_unit * self.sign,
                'sequence': self.sequence}


class ShippingLineBuilder(Component):
    """ Return values for a Shipping line """

    _name = 'ecommerce.order.line.builder.shipping'
    _inherit = 'ecommerce.order.line.builder'
    _usage = 'order.line.builder.shipping'

    def __init__(self, work_context):
        super(ShippingLineBuilder, self).__init__(work_context)
        self.product_ref = ('connector_ecommerce', 'product_product_shipping')
        self.sequence = 999

    def get_line(self):
        values = super(ShippingLineBuilder, self).get_line()
        values['is_delivery'] = True
        return values


class CashOnDeliveryLineBuilder(Component):
    """ Return values for a Cash on Delivery line """

    _name = 'ecommerce.order.line.builder.cod'
    _inherit = 'ecommerce.order.line.builder'
    _usage = 'order.line.builder.cod'

    def __init__(self, work_context):
        super(CashOnDeliveryLineBuilder, self).__init__(work_context)
        self.product_ref = ('connector_ecommerce',
                            'product_product_cash_on_delivery')
        self.sequence = 995


class GiftOrderLineBuilder(Component):
    """ Return values for a Gift line """

    _name = 'ecommerce.order.line.builder.gift'
    _inherit = 'ecommerce.order.line.builder'
    _usage = 'order.line.builder.gift'

    def __init__(self, work_context):
        super(GiftOrderLineBuilder, self).__init__(work_context)
        self.product_ref = ('connector_ecommerce',
                            'product_product_gift')
        self.sign = -1
        self.gift_code = None
        self.sequence = 990

    def get_line(self):
        line = super(GiftOrderLineBuilder, self).get_line()
        if self.gift_code:
            line['name'] = "%s [%s]" % (line['name'], self.gift_code)
        return line
