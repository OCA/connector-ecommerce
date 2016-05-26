# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2011-2013 Akretion
#    @author Sébastien BEAU <sebastien.beau@akretion.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models


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
