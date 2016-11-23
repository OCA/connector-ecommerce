# -*- coding: utf-8 -*-
# © 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models
from odoo.addons.connector.connector import ConnectorUnit


class SpecialOrderLineBuilder(ConnectorUnit):
    """ Base class to build a sales order line for a sales order

    Used when extra order lines have to be added in a sales order
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

    def __init__(self, connector_env):
        super(SpecialOrderLineBuilder, self).__init__(connector_env)
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


class ShippingLineBuilder(SpecialOrderLineBuilder):
    """ Return values for a Shipping line """
    _model_name = None

    def __init__(self, connector_env):
        super(ShippingLineBuilder, self).__init__(connector_env)
        self.product_ref = ('connector_ecommerce', 'product_product_shipping')
        self.sequence = 999


class CashOnDeliveryLineBuilder(SpecialOrderLineBuilder):
    """ Return values for a Cash on Delivery line """
    _model_name = None

    def __init__(self, connector_env):
        super(CashOnDeliveryLineBuilder, self).__init__(connector_env)
        self.product_ref = ('connector_ecommerce',
                            'product_product_cash_on_delivery')
        self.sequence = 995


class GiftOrderLineBuilder(SpecialOrderLineBuilder):
    """ Return values for a Gift line """
    _model_name = None

    def __init__(self, connector_env):
        super(GiftOrderLineBuilder, self).__init__(connector_env)
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
