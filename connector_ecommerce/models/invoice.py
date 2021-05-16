# © 2013 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        super().action_post()
        self.notify_invoice_validate()

    def action_invoice_paid(self):
        res = super().action_invoice_paid()
        for record in self:
            self._event("on_invoice_paid").notify(record)
        return res

    def notify_invoice_validate(self):
        for record in self.filtered(lambda m: m.move_type == "out_invoice"):
            self._event("on_invoice_validated").notify(record)
