# -*- coding: utf-8 -*-
# © 2011-2013 Akretion (Sébastien Beau)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api


class AccountPaymentMode(models.Model):
    _inherit = "account.payment.mode"

    @api.model
    def _get_import_rules(self):
        return [('always', 'Always'),
                ('never', 'Never'),
                ('paid', 'Paid'),
                ('authorized', 'Authorized'),
                ]

    # the logic around the 2 following fields has to be implemented
    # in the connectors (magentoerpconnect, prestashoperpconnect,...)
    days_before_cancel = fields.Integer(
        string='Days before cancel',
        default=30,
        help="After 'n' days, if the 'Import Rule' is not fulfilled, the "
             "import of the sales order will be canceled.",
    )
    import_rule = fields.Selection(selection='_get_import_rules',
                                   string="Import Rule",
                                   default='always',
                                   required=True)

    @api.model
    def get_or_create_payment_method(self, payment_method):
        """ Try to get a payment method or create if it doesn't exist

        :param payment_method: payment method like PayPal, etc.
        :type payment_method: str
        :return: required payment method
        :rtype: recordset
        """
        domain = [('name', '=ilike', payment_method)]
        method = self.search(domain, limit=1)
        if not method:
            method = self.create({'name': payment_method})
        return method
