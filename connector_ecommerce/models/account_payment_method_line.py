# © 2011-2013 Akretion (Sébastien Beau)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class AccountPaymentMethodLine(models.Model):
    _inherit = "account.payment.method.line"

    # the logic around the 2 following fields has to be implemented
    # in the connectors (magentoerpconnect, prestashoperpconnect,...)
    days_before_cancel = fields.Integer(
        default=30,
        help="After 'n' days, if the 'Import Rule' is not fulfilled, the "
        "import of the sales order will be canceled.",
    )
    import_rule = fields.Selection(
        selection=lambda self: self._selection_import_rule(),
        default="always",
        required=True,
        help="""
            - Never: the sales orders using the payment method will never be imported.
            - Always: the sales orders using the payment method will always be imported.
            - Paid: the sales orders using the payment method will be imported
                    only when they receive a payment on the E-Commerce backend.
        """,
    )

    @api.model
    def _selection_import_rule(self):
        return [
            ("always", "Always"),
            ("never", "Never"),
            ("paid", "Paid"),
            ("authorized", "Authorized"),
        ]
