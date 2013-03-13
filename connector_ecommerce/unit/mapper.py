
# -*- coding: utf-8 -*-
###############################################################################
#
#   connector-ecommerce for OpenERP
#   Copyright (C) 2013-TODAY Akretion <http://www.akretion.com>.
#     All Rights Reserved
#     @author Sébastien BEAU <sebastien.beau@akretion.com>
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp.addons.connector.unit.mapper import ImportMapper


class SaleOrderImportMapper(ImportMapper):

    def _prepare_order_params(self, result):
        args = [None, result['partner_id']]
        kwargs = {'context': self.session.context}
        return args, kwargs

    def _play_order_onchange(self, result):
        sale_model = self.session.pool.get('sale.order')
        args, kwargs = self._prepare_order_params(result)
        onchange = sale_model.onchange_partner_id(self.session.cr,
                self.session.uid, *args, **kwargs)
        vals = onchange.get('value')
        for key in vals:
            if not key in result:
                result[key] = vals[key]
        return result
 
    def _prepare_line_params(self, line, previous_line, order):
        args = [
            None, #ids
            order.get('pricelist_id'),
            line.get('product_id')
        ]
        kwargs ={
            'qty': float(line.get('product_uom_qty')),
            'uom': line.get('product_uom'),
            'qty_uos': float(line.get('product_uos_qty') or line.get('product_uom_qty')),
            'uos': line.get('product_uos'),
            'name': line.get('name'),
            'partner_id': order.get('partner_id'),
            'lang': False,
            'update_tax': True,
            'date_order': order.get('date_order'),
            'packaging': line.get('product_packaging'),
            'fiscal_position': order.get('fiscal_position'),
            'flag': False,
            'context': self.session.context,
        }
        return args, kwargs

    def _play_line_onchange(self, line, previous_line, order):
        sale_line_model = self.session.pool.get('sale.order.line')
        args, kwargs = self._prepare_line_params(line, previous_line, order)
        onchange = sale_line_model.product_id_change(self.session.cr,
                self.session.uid, *args, **kwargs)
        vals = onchange.get('value')
        for key in vals:
            if not key in line:
                #TODO support correct m2m [(6, 0, line['tax_id'])]
                line[key] = vals[key]
        return line

    def _after_mapping(self, result):
        result = super(SaleOrderImportMapper, self)._after_mapping(result)
        result = self._play_order_onchange(result)

        order_lines = []
        for line in result['order_line']:
            order_lines.append((0, 0,
                self._play_line_onchange(line[2], order_lines, result)))
        result['order_line'] = order_lines 
        return result

