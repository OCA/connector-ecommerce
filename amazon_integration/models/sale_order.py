from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    amazon_reference = fields.Char(
        string='Amazon Reference')

    amazon_fulfillment = fields.Selection(
        [('fbm', 'FBM'),
         ('fba', 'FBA')],
        string='Amazon Fulfillment')

    amazon_marketplace_id = fields.Many2one(
        comodel_name='amazon.marketplace',
        string='Amazon Marketplace')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    amazon_order_item_id = fields.Char(
        string='Amazon Order Item Id')
