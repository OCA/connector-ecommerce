# -*- coding: utf-8 -*-
# © 2013 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp import models, api
from openerp.addons.connector.session import ConnectorSession
from .event import on_invoice_paid, on_invoice_validated


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def confirm_paid(self):
        res = super(AccountInvoice, self).confirm_paid()
        session = ConnectorSession.from_env(self.env)
        for record_id in self.ids:
            on_invoice_paid.fire(session, self._name, record_id)
        return res

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        session = ConnectorSession.from_env(self.env)
        for record_id in self.ids:
            on_invoice_validated.fire(session, self._name, record_id)
        return res
