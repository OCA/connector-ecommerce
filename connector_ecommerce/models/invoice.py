# -*- coding: utf-8 -*-
# © 2013 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, api
from .event import on_invoice_paid, on_invoice_validated


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_invoice_paid(self):
        res = super(AccountInvoice, self).action_invoice_paid()
        for record_id in self.ids:
            on_invoice_paid.fire(self.env, self._name, record_id)
        return res

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        for record_id in self.ids:
            on_invoice_validated.fire(self.env, self._name, record_id)
        return res
