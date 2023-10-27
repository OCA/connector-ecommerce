# © 2011-2013 Akretion (Sébastien Beau)
# © 2018 FactorLibre
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # TODO implement set function and also support multi tax
    @api.depends("taxes_id.tax_group_id")
    def _compute_tax_group_id(self):
        self.ensure_one()
        taxes = self.taxes_id
        self.tax_group_id = taxes[:-1].tax_group_id.id

    tax_group_id = fields.Many2one(
        comodel_name="account.tax.group",
        compute="_compute_tax_group_id",
        string="Tax Group",
        help="Tax groups are used with some external system like Prestashop",
    )

    @api.model
    def _price_changed_fields(self):
        return {"list_price", "lst_price", "standard_price"}

    def _price_changed(self, vals):
        """Fire the ``on_product_price_changed`` on all the variants of
        the template if the price of the product could have changed.

        If one of the field used in a sale pricelist item has been
        modified, we consider that the price could have changed.

        There is no guarantee that's the price actually changed,
        because it depends on the pricelists.
        """
        price_fields = self._price_changed_fields()
        if any(field in vals for field in price_fields):
            product_model = self.env["product.product"]
            products = product_model.search([("product_tmpl_id", "in", self.ids)])
            # when the write is done on the product.product, avoid
            # to fire the event 2 times
            if self.env.context.get("from_product_ids"):
                from_product_ids = self.env.context["from_product_ids"]
                remove_products = product_model.browse(from_product_ids)
                products -= remove_products
            for product in products:
                self._event("on_product_price_changed").notify(product)

    def write(self, vals):
        result = super(ProductTemplate, self).write(vals)
        self._price_changed(vals)
        return result


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _price_changed_fields(self):
        return {"lst_price", "standard_price", "price", "price_extra"}

    def _price_changed(self, vals):
        """Fire the ``on_product_price_changed`` if the price
        of the product could have changed.

        If one of the field used in a sale pricelist item has been
        modified, we consider that the price could have changed.

        There is no guarantee that's the price actually changed,
        because it depends on the pricelists.
        """
        price_fields = self._price_changed_fields()
        if any(field in vals for field in price_fields):
            for product in self:
                self._event("on_product_price_changed").notify(product)

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
