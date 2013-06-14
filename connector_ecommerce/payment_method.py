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

from openerp.osv import orm, fields


class payment_method(orm.Model):
    _inherit = "payment.method"

    def _get_import_rules(self, cr, uid, context=None):
        return [('always', 'Always'),
                ('never', 'Never'),
                ('paid', 'Paid'),
                ('authorized', 'Authorized'),
                ]

    _columns = {
        # the logic around the 2 following fields has to be implemented
        # in the connectors (magentoerpconnect, prestashoperpconnect,...)
        'days_before_cancel': fields.integer(
            'Days before cancel',
            help="After 'n' days, if the 'Import Rule' is not fulfilled, the "
                 "import of the sale order will be canceled."),
        'import_rule': fields.selection(_get_import_rules,
                                        string="Import Rule",
                                        required=True)
    }

    _defaults = {
        'import_rule': 'always',
        'days_before_cancel': 30,
    }

    def get_or_create_payment_method(self, cr, uid, payment_method, context=None):
        """
        try to get id of 'payment_method' or create if not exists
        :param str payment_method: payment method like PayPal, etc.
        :rtype: int
        :return: id of required payment method
        """
        pay_method_obj = self.pool.get('payment.method')
        method_ids = pay_method_obj.search(cr, uid,
                                           [('name', '=ilike', payment_method)],
                                           context=context)
        if method_ids:
            method_id = method_ids[0]
        else:
            method_id = pay_method_obj.create(cr, uid,
                                              {'name': payment_method},
                                              context=context)
        return method_id
