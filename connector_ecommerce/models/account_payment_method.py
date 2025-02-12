# © 2011-2013 Akretion (Sébastien Beau)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import re

from odoo import api, models


class AccountPaymentMethod(models.Model):
    _inherit = "account.payment.method"

    @api.model
    def _get_payment_method_domain(self, payment_method):
        """Return the domain for searching a payment method."""
        return [("name", "=ilike", payment_method)]

    @api.model
    def _sanitize_payment_method_code(self, payment_method):
        """Convert payment method name into a suitable code format."""
        return re.sub(r"[^a-z0-9]+", "_", payment_method.lower()).strip("_")

    @api.model
    def _prepare_payment_method_vals(self, payment_method):
        """Prepare values for creating a new payment method."""
        return {
            "name": payment_method,
            "code": self._sanitize_payment_method_code(payment_method),
            "payment_type": "inbound",
        }

    @api.model
    def get_or_create_payment_method(self, payment_method):
        """Try to get a payment method or create if it doesn't exist

        :param payment_method: payment method like PayPal, etc.
        :type payment_method: str
        :return: required payment method
        :rtype: recordset
        """
        domain = self._get_payment_method_domain(payment_method)
        method = self.search(domain, limit=1)
        if not method:
            method = self.create([self._prepare_payment_method_vals(payment_method)])
        return method
