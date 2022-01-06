from odoo import models, fields
from mws import Sellers, Orders
from dateutil.parser import parse
from datetime import datetime
import time
from dateutil import parser
import pytz
utc = pytz.utc


class AmazonSeller(models.Model):
    _name = 'amazon.seller'
    _description = 'Account for Amazon MWS'

    name = fields.Char(
        string='Name',
        required=True)

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env['res.company']._company_default_get(
            'amazon.seller'))

    access_key = fields.Char(
        string='Access Key')

    secret_key = fields.Char(
        string='Secret Key')

    merchant_id = fields.Char(
        string='Merchant ID')

    country_id = fields.Many2one(
        comodel_name='res.country',
        string='Country',
        required=True)

    marketplace_ids = fields.One2many(
        comodel_name='amazon.marketplace',
        inverse_name='seller_id',
        string='Marketplaces')

    last_import_date_seller = fields.Datetime(
        string='Last Import Date',
        default=datetime.now(),
        help='Date from the last order synced')

    def get_marketplaces(self):
        mws_connection = Sellers(access_key=str(self.access_key),
                                 secret_key=str(self.secret_key),
                                 account_id=str(self.merchant_id),
                                 region=self.country_id.code,
                                 )
        marketplace_obj = self.env['amazon.marketplace']
        pricelist_obj = self.env['product.pricelist']
        lang_obj = self.env['res.lang']
        country_obj = self.env['res.country']
        list_result = []
        try:
            result = mws_connection.list_marketplace_participations()
            result.parsed.get('ListParticipations', {})
        except Exception as e:
            raise Warning('Given Credentials is incorrect, \
                please provide correct Credentials.' + str(e))

        list_result.append(result)
        next_token = result.parsed.get('NextToken', {}).get('value')
        while next_token:
            try:
                result = mws_connection.\
                    list_marketplace_participations_by_next_token(next_token)
            except Exception as e:
                raise Warning(str(e))
            next_token = result.parsed.get('NextToken', {}).get('value')
            list_result.append(result)

        for element in list_result:
            element = element.parsed
            list_marketplaces = element.get('ListMarketplaces', {})
            marketplaces = list_marketplaces.get('Marketplace', [])
            if not isinstance(marketplaces, list):
                marketplaces = [marketplaces]

            for marketplace in marketplaces:
                marketplace_id = marketplace.get(
                    'MarketplaceId', {}).get('value', '')
                country_code = marketplace.get('DefaultCountryCode', {}).get(
                    'value')
                name = marketplace.get('Name', {}).get('value', '')
                lang_code = marketplace.get(
                    'DefaultLanguageCode', {}).get('value', '')
                currency_code = marketplace.get(
                    'DefaultCurrencyCode', {}).get('value', '')
                pricelist_id = pricelist_obj.search([(
                    'name', '=', currency_code)])
                lang_id = lang_obj.search([('code', '=', lang_code)])
                country_id = country_obj.search([('code', '=', country_code)])

                vals = {
                    'seller_id': self.id,
                    'name': name,
                    'market_code': marketplace_id,
                    'pricelist_id': pricelist_id and pricelist_id[0].id or
                    False,
                    'lang_id': lang_id and lang_id[0].id or False,
                    'country_id': country_id and country_id[0].id or
                    self.country_id and self.country_id.id or False,
                    'company_id': self.company_id.id,
                }
                marketplace_rec = marketplace_obj.search(
                    [('seller_id', '=', self.id),
                     ('market_code', '=', marketplace_id)])
                if marketplace_rec:
                    marketplace_rec.write(vals)
                else:
                    marketplace_obj.create(vals)
        return True

    # Create FBM and FBA orders
    def action_import_orders(self):
        self.import_orders()

    def import_orders(self, marketplaces=False, seller=False,
                      last_import_date=False, single_market=False):
        if not seller:
            seller = self.env['amazon.seller'].search([], limit=1)
        if not marketplaces:
            marketplaces = seller.marketplace_ids
        if not last_import_date:
            last_import_date = seller.last_import_date_seller.isoformat(
                sep='T')
        else:
            last_import_date = last_import_date.isoformat(sep='T')

        mws_obj = Orders(access_key=str(seller.access_key),
                         secret_key=str(seller.secret_key),
                         account_id=str(seller.merchant_id),
                         region=seller.country_id.code
                         )

        has_next = True
        next_token = None
        orders_data = []
        market_obj = self.env['amazon.marketplace']
        marketplaceids = marketplaces.mapped('market_code')
        orderstatus = ('Unshipped', 'PartiallyShipped', 'Shipped')
        while has_next:
            time.sleep(1)
            order_data = mws_obj.list_orders(
                marketplaceids=marketplaceids,
                created_after=last_import_date,
                orderstatus=orderstatus,
                next_token=next_token,
            )
            orders = order_data.parsed.get('Orders', {}).get('Order', [])
            if orders and isinstance(orders, dict):
                orders_data.append(orders)
            elif orders and isinstance(orders, list):
                orders_data += orders
            for order in orders_data:
                market_code = order.get(
                    'MarketplaceId', {}).get(
                    'value', False)
                marketplace = market_obj.search([
                    ('market_code', '=', market_code)])
                sale_channel = order.get(
                    'SalesChannel', {}).get(
                    'value', 'sale')
                if sale_channel == 'Non-Amazon':
                    continue
                seller._create_sale_order(order, marketplace, mws_obj)
                # Date to synchronize every time an order is imported
                last_purchase_date = order.get('PurchaseDate').get('value')
                last_purchase_date = parse(
                    last_purchase_date).replace(tzinfo=None)
                if single_market:
                    marketplace.last_import_date = last_purchase_date
                else:
                    seller.last_import_date_seller = last_purchase_date
                    marketplace.last_import_date = last_purchase_date
            # commit a batch of 100 orders due to request throttled from Amazon
            self.env.cr.commit()
            next_token = order_data.parsed.get('NextToken', {}).get('value')
            has_next = bool(next_token)

    def _create_sale_order(self, order, marketplace, mws_obj):
        IrDefault = self.env['ir.default'].sudo()
        amazon_user = IrDefault.get('res.config.settings', 'amazon_user_id')
        sale_obj = self.env['sale.order']
        amazon_order_ref = order.get('AmazonOrderId').get('value')
        fulfillment_channel = order.get('FulfillmentChannel').get('value')
        amazon_fulfillment = 'fba' if fulfillment_channel == 'AFN' else 'fbm'
        date_order = parser.parse(
            order.get('PurchaseDate').get('value')).astimezone(utc)
        pricelist = marketplace.pricelist_id
        invoice_partner, delivery_partner = self._get_partner(order)
        order_found = sale_obj.search([
            ('amazon_reference', '=', amazon_order_ref)])
        if not order_found:
            ord_lines = self._create_sale_order_lines(
                amazon_order_ref, marketplace, mws_obj)
            order = sale_obj.create({
                'origin': amazon_order_ref,
                'date_order': date_order,
                'partner_id': invoice_partner.id,
                'partner_shipping_id': delivery_partner.id,
                'pricelist_id': pricelist.id,
                'order_line': [(0, 0, order_line) for order_line in ord_lines],
                'fiscal_position_id': marketplace.fiscal_position_id.id,
                'amazon_reference': amazon_order_ref,
                'amazon_fulfillment': amazon_fulfillment,
                'company_id': self.company_id.id,
                'user_id': amazon_user,
                'amazon_marketplace_id': marketplace.id,
                'payment_term_id': marketplace.payment_term_id.id,
            })

    def _get_partner(self, order):
        partner_obj = self.env['res.partner']
        country_obj = self.env['res.country']
        lang_obj = self.env['res.lang']
        state_obj = self.env['res.country.state']
        shipping_address = order.get('ShippingAddress', {})
        country_code = shipping_address.get('CountryCode', {}).get('value')
        country = country_obj.search([('code', '=', country_code)], limit=1)
        lang = False
        if country_code:
            country_code_lower = country_code.lower()
            lang = lang_obj.search([('iso_code', '=', country_code_lower)])
        state_code = shipping_address.get(
            'StateOrRegion', {}).get('value', False)
        state = state_obj.search([
            ('country_id', '=', country.id), '|',
            ('code', '=', state_code),
            ('name', '=', state_code)],
            limit=1)
        if not state and country and state_code:
            state = state_obj.create({
                'country_id': country.id,
                'name': state_code,
                'code': state_code
            })
        street = shipping_address.get('AddressLine1', {}).get('value', False)
        street2 = shipping_address.get('AddressLine2', {}).get('value', False)
        postalcode = shipping_address.get('PostalCode', {}).get('value', False)
        deliv_name = shipping_address.get('Name', {}).get('value', False)
        phone = shipping_address.get('Phone', {}).get('value', False)
        city = shipping_address.get('City', {}).get('value', False)
        email = order.get('BuyerEmail', {}).get('value', False)
        invoice_name = order.get('BuyerName', {}).get('value', False)
        domain = []
        street and domain.append(('street', '=', street))
        street2 and domain.append(('street2', '=', street2))
        email and domain.append(('email', '=', email))
        phone and domain.append(('phone', '=', phone))
        city and domain.append(('city', '=', city))
        postalcode and domain.append(('zip', '=', postalcode))
        state and domain.append(('state_id', '=', state.id))
        country and domain.append(('country_id', '=', country.id))
        deliv_name and domain.append(('name', '=', deliv_name))
        domain.append(('type', '=', 'delivery'))
        delivery_vals = {
            'name': deliv_name,
            'is_company': False,
            'customer': True,
            'street': street,
            'street2': street2,
            'city': city,
            'country_id': country.id,
            'type': 'delivery',
            'phone': phone,
            'zip': postalcode,
            'state_id': state.id,
            'email': email,
            'lang': lang.code,
            'company_id': self.company_id.id
        }
        delivery_partner = partner_obj.search(domain, limit=1)
        if not delivery_partner:
            delivery_partner = partner_obj.create(delivery_vals)
        domain.remove(('name', '=', deliv_name))
        domain.append(('name', '=', invoice_name))
        domain.remove(('type', '=', 'delivery'))
        domain.append(('type', '=', 'invoice'))
        invoice_partner = partner_obj.search(domain, limit=1)
        if not invoice_partner:
            if email:
                invoice_partner = partner_obj.search([
                    ('email', '=', email),
                    ('type', '=', 'invoice')],
                    limit=1)
            if phone and not invoice_partner:
                invoice_partner = partner_obj.search([
                    ('phone', '=', phone),
                    ('type', '=', 'invoice')],
                    limit=1)
            if not invoice_partner:
                invoice_partner_vals = {
                    'name': invoice_name,
                    'is_company': False,
                    'customer': True,
                    'street': street,
                    'street2': street2,
                    'city': city,
                    'country_id': country.id,
                    'type': 'invoice',
                    'phone': phone,
                    'zip': postalcode,
                    'state_id': state.id,
                    'email': email,
                    'lang': lang.code,
                    'company_id': self.env.user.company_id.id
                }
                invoice_partner = partner_obj.create(invoice_partner_vals)
        delivery_partner.parent_id = invoice_partner.id
        return invoice_partner, delivery_partner

    def _create_sale_order_lines(self, amazon_order_ref, marketplace,
                                 mws_obj):
        product_obj = self.env['product.product']
        shipment_product_id = product_obj.search(
            [('default_code', '=', 'SHIP AMAZON')], limit=1)
        gift_product_id = product_obj.search(
            [('default_code', '=', 'GIFT AMAZON')], limit=1)
        not_found_product_id = product_obj.search(
            [('default_code', '=', 'Amazon Not Found')], limit=1)
        has_next = True
        next_token = None
        while has_next:
            time.sleep(1)
            order_items_data = mws_obj.list_order_items(
                amazon_order_id=amazon_order_ref,
                next_token=next_token,
            )
            order_line_vals = []
            order_items_parsed = order_items_data.parsed
            order_items = order_items_parsed.get('OrderItems').get('OrderItem')
            lines = []
            if isinstance(order_items, dict):
                lines.append(order_items)
            elif isinstance(order_items, list):
                lines += order_items
            for item in lines:
                sku = item.get('SellerSKU').get('value')
                product = self.get_product(sku)
                if not product:
                    product = not_found_product_id
                # Order Lines
                order_line_vals = self.get_item_values(
                    item, product, order_line_vals, marketplace)
                shipping = item.get('ShippingPrice')
                gift = item.get('GiftWrapPrice')
                if shipping:
                    order_line_vals = self.get_shipping_values(
                        item, shipment_product_id, order_line_vals,
                        marketplace)
                if gift:
                    order_line_vals = self.get_gift_values(
                        item, gift_product_id, order_line_vals,
                        marketplace)
            next_token = order_items_parsed.get('NextToken', {}).get('value')
            has_next = bool(next_token)
        return order_line_vals

    def get_product(self, sku):
        return self.env['product.product'].search([('default_code', '=', sku)],
                                                  limit=1)

    def get_item_values(self, item, product, order_line_vals, marketplace):
        quantity = float(item.get('QuantityOrdered').get('value'))
        item_price = float(item.get('ItemPrice').get('Amount').get('value'))
        description = item.get('Title').get('value')
        fiscal_position = marketplace.fiscal_position_id
        product_tax = product.taxes_id.filtered(
            lambda x: x.company_id.id == self.company_id.id)
        tax = fiscal_position.map_tax(product_tax)
        tax_reduce = tax.amount / 100 + 1
        item_price = item_price / tax_reduce
        promotion_discount = float(
            item.get('PromotionDiscount').get('Amount').get('value'))
        if promotion_discount:
            promotion_discount = promotion_discount / tax_reduce
        amazon_order_item_id = item.get('OrderItemId').get('value')
        item_vals = {
            'product_id': product.id,
            'product_uom_qty': quantity,
            'name': description,
            'tax_id': [(6, 0, tax.ids)],
            'price_unit': item_price,
            'discount': (promotion_discount / item_price) * 100,
            'amazon_order_item_id': amazon_order_item_id,
        }
        order_line_vals.append(item_vals)
        return order_line_vals

    def get_shipping_values(self, item, shipment_product_id,
                            order_line_vals, marketplace):
        fiscal_position = marketplace.fiscal_position_id
        product_tax = shipment_product_id.taxes_id.filtered(
            lambda x: x.company_id.id == self.company_id.id)
        tax = fiscal_position.map_tax(product_tax)
        tax_reduce = tax.amount / 100 + 1
        shipping_price = float(
            item.get('ShippingPrice').get('Amount').get('value'))
        shipping_price = shipping_price / tax_reduce
        shipping_discount = float(
            item.get('ShippingDiscount').get('Amount').get('value'))
        if shipping_discount:
            shipping_discount = shipping_discount / tax_reduce
        item_shipping_vals = {
            'product_id': shipment_product_id.id,
            'product_uom_qty': 1,
            'tax_id': [(6, 0, tax.ids)],
            'price_unit': shipping_price,
            'discount': (shipping_discount / shipping_price) * 100,
        }
        order_line_vals.append(item_shipping_vals)
        return order_line_vals

    def get_gift_values(self, item, gift_product_id,
                        order_line_vals, marketplace):
        fiscal_position = marketplace.fiscal_position_id
        product_tax = gift_product_id.taxes_id.filtered(
            lambda x: x.company_id.id == self.company_id.id)
        tax = fiscal_position.map_tax(product_tax)
        tax_reduce = tax.amount / 100 + 1
        gift_wrap_price = float(
            item.get('GiftWrapPrice').get('Amount').get('value'))
        gift_wrap_price = gift_wrap_price / tax_reduce
        item_gift_vals = {
            'product_id': gift_product_id.id,
            'product_uom_qty': 1,
            'tax_id': [(6, 0, tax.ids)],
            'price_unit': gift_wrap_price,
        }
        order_line_vals.append(item_gift_vals)
        return order_line_vals
