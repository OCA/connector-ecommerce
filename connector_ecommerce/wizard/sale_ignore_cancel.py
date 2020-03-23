# © 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class SaleIgnoreCancel(models.TransientModel):
    _name = "sale.ignore.cancel"
    _description = "Ignore Sales Order Cancel"

    reason = fields.Html(required=True)

    def confirm_ignore_cancel(self):
        self.ensure_one()
        sale_ids = self.env.context.get("active_ids")
        assert sale_ids
        sales = self.env["sale.order"].browse(sale_ids)
        sales.ignore_cancellation(self.reason)
        return {"type": "ir.actions.act_window_close"}
