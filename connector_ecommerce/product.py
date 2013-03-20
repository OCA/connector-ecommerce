# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Sébastien BEAU
#    Copyright 2011-2013 Akretion
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


class product_template(orm.Model):
    _inherit = 'product.template'

    #TODO implement set function and also support multi tax
    def _get_tax_group_id(self, cr, uid, ids, field_name, args, context=None):
        result = {}
        for product in self.browse(cr, uid, ids, context=context):
            taxes = product.taxes_id
            result[product.id] = taxes[0].group_id.id if taxes else False
        return result

    _columns = {
        'tax_group_id': fields.function(
                            _get_tax_group_id,
                            string='Tax Group',
                            type='many2one',
                            relation='account.tax.group',
                            store=False,
                            help='Tax group are used with some external '
                                 'system like magento or prestashop'),
    }
