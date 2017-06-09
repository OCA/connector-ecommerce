# -*- coding: utf-8 -*-
# © 2011-2013 Akretion (Sébastien Beau)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api
from .event import on_product_price_changed


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # TODO implement set function and also support multi tax
    @api.one
    @api.depends('taxes_id.tax_group_id')
    def _compute_tax_group_id(self):
        taxes = self.taxes_id
        self.tax_group_id = taxes[:-1].tax_group_id.id
    tax_group_id = fields.Many2one(
        comodel_name='account.tax.group',
        compute='_compute_tax_group_id',
        string='Tax Group',
        help='Tax groups are used with some external '
             'system like Prestashop',
    )

    @api.model
    def _price_changed_fields(self):
        return {'list_price', 'lst_price', 'standard_price'}

    @api.multi
    def _price_changed(self, vals):
        """ Fire the ``on_product_price_changed`` on all the variants of
        the template if the price of the product could have changed.

        If one of the field used in a sale pricelist item has been
        modified, we consider that the price could have changed.

        There is no guarantee that's the price actually changed,
        because it depends on the pricelists.
        """
        price_fields = self._price_changed_fields()
        if any(field in vals for field in price_fields):
            product_model = self.env['product.product']
            products = product_model.search(
                [('product_tmpl_id', 'in', self.ids)]
            )
            # when the write is done on the product.product, avoid
            # to fire the event 2 times
            if self.env.context.get('from_product_ids'):
                from_product_ids = self.env.context['from_product_ids']
                remove_products = product_model.browse(from_product_ids)
                products -= remove_products
            for product in products:
                self._event('on_product_price_changed').notify(product)
                # deprecated:
                on_product_price_changed.fire(self.env,
                                              product_model._name,
                                              product.id)

    @api.multi
    def write(self, vals):
        result = super(ProductTemplate, self).write(vals)
        self._price_changed(vals)
        return result


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.depends()
    def _compute_has_checkpoint(self):
        checkpoint_model = self.env['connector.checkpoint']
        model_model = self.env['ir.model']
        model = model_model.search([('model', '=', 'product.product')])
        for product in self:
            points = checkpoint_model.search([('model_id', '=', model.id),
                                              ('record_id', '=', product.id),
                                              ('state', '=', 'need_review')],
                                             limit=1,
                                             )
            product.has_checkpoint = bool(points)

    has_checkpoint = fields.Boolean(compute='_compute_has_checkpoint',
                                    string='Has Checkpoint')

    @api.model
    def _price_changed_fields(self):
        return {'lst_price', 'standard_price', 'price', 'price_extra'}

    @api.multi
    def _price_changed(self, vals):
        """ Fire the ``on_product_price_changed`` if the price
        of the product could have changed.

        If one of the field used in a sale pricelist item has been
        modified, we consider that the price could have changed.

        There is no guarantee that's the price actually changed,
        because it depends on the pricelists.
        """
        price_fields = self._price_changed_fields()
        if any(field in vals for field in price_fields):
            for product in self:
                self._event('on_product_price_changed').notify(product)
                # deprecated:
                on_product_price_changed.fire(self.env, self._name, product.id)

    @api.multi
    def write(self, vals):
        self_context = self.with_context(from_product_ids=self.ids)
        result = super(ProductProduct, self_context).write(vals)
        self._price_changed(vals)
        return result

    @api.model
    def create(self, vals):
        product = super(ProductProduct, self).create(vals)
        product._price_changed(vals)
        return product
