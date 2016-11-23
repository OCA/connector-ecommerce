# -*- coding: utf-8 -*-
# © 2011-2013 Akretion (Sébastien Beau)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class AccountTaxCode(models.Model):
    _inherit = 'account.tax'

    def get_tax_from_rate(self, rate, is_tax_included=False):
        account_tax_model = self.env['account.tax']
        tax = account_tax_model.search(
            [('price_include', '=', is_tax_included),
             ('type_tax_use', 'in', ['sale', 'all']),
             ('amount', '>=', rate - 0.001),
             ('amount', '<=', rate + 0.001)],
            limit=1,
        )
        if tax:
            return tax

        # try to find a tax with less precision
        tax = account_tax_model.search(
            [('price_include', '=', is_tax_included),
             ('type_tax_use', 'in', ['sale', 'all']),
             ('amount', '>=', rate - 0.01),
             ('amount', '<=', rate + 0.01)],
            limit=1,
        )
        return tax
