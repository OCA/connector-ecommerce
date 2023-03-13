# © 2013 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        res = super().action_post()
        self.notify_invoice_validate()
        return res

    def _invoice_paid_hook(self):
        res = super()._invoice_paid_hook()
        for record in self:
            self._event("on_invoice_paid").notify(record)
        return res

    def notify_invoice_validate(self):
        for record in self:
            if record.move_type != "out_invoice":
                continue
            self._event("on_invoice_validated").notify(record)
