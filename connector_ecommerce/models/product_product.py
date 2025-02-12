# © 2011-2013 Akretion (Sébastien Beau)
# © 2018 FactorLibre
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _price_changed_fields(self):
        return {
            "lst_price",
            "price_extra",
        } | self.product_tmpl_id._price_changed_fields()

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

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for vals, record in zip(vals_list, records, strict=True):
            record._price_changed(vals)
        return records
