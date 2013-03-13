# -*- coding: utf-8 -*-
###############################################################################
#
#   connector-ecommerce for OpenERP
#   Copyright (C) 2013-TODAY Akretion <http://www.akretion.com>.
#     @author Sébastien BEAU <sebastien.beau@akretion.com>
#
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

from openerp.addons.connector.connector import ConnectorUnit

class SaleOrderOnChange(ConnectorUnit):
    # name of the OpenERP model, to be defined in concrete classes
    _model_name = None

    def _get_partner_id_onchange_param(self, order):
        """ Prepare the arguments for calling the partner_id change
        on sale order. You can overwrite this method in your own
        module if they modify the onchange signature
 
        :param order: a dictionnary of the value of your sale order
        :type: dict
        
        :return: a tuple of args and kwargs for the onchange
        :rtype: tuple
        """
        args = [
            None, # sale order ids not needed
            order['partner_id'],
        ]
        kwargs = {'context': self.session.context}
        return args, kwargs

    def _play_order_onchange(self, order):
        """ Play the onchange of the sale order
 
        :param order: a dictionnary of the value of your sale order
        :type: dict
        
        :return: the value of the sale order updated with the onchange result
        :rtype: dict
        """
        sale_model = self.session.pool.get('sale.order')
        
        #Play partner_id onchange
        args, kwargs = self._get_partner_id_onchange_param(order)
        res = sale_model.onchange_partner_id(self.session.cr,
                self.session.uid, *args, **kwargs)
        vals = res.get('value')
        for key in vals:
            if not key in order:
                order[key] = vals[key]

        return order
 
    def _get_product_id_onchange_param(self, line, previous_line, order):
        """ Prepare the arguments for calling the product_id change
        on sale order line. You can overwrite this method in your own
        module if they modify the onchange signature
 
        :param line: the sale order line to process
        :type: dict
        :param previous_line: list of dict of the previous line processed
        :type: list
        :param order: data of the sale order
        :type: dict

        :return: a tuple of args and kwargs for the onchange
        :rtype: tuple
        """
        args = [
            None, # sale order line ids not needed
            order.get('pricelist_id'),
            line.get('product_id')
        ]
        kwargs ={
            'qty': float(line.get('product_uom_qty')),
            'uom': line.get('product_uom'),
            'qty_uos': float(line.get('product_uos_qty')\
                    or line.get('product_uom_qty')),
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
        """ Play the onchange of the sale order line
 
        :param line: the sale order line to process
        :type: dict
        :param previous_line: list of dict of the previous line processed
        :type: list
        :param order: data of the sale order
        :type: dict
        
        :return: the value of the sale order updated with the onchange result
        :rtype: dict
        """
        sale_line_model = self.session.pool.get('sale.order.line')

        #Play product_id onchange
        args, kwargs = self._get_product_id_onchange_param(line,
                                        previous_line, order)
        res = sale_line_model.product_id_change(self.session.cr,
                self.session.uid, *args, **kwargs)
        vals = res.get('value')
        for key in vals:
            if not key in line:
                if sale_line_model._columns[key]._type == 'many2many':
                    line[key] = [(6, 0, vals[key])]
                else:
                    line[key] = vals[key]
        return line

    def play(self, order):
        """ Play the onchange of the sale order and it's lines
 
        :param order: data of the sale order
        :type: dict
        
        :return: the value of the sale order updated with the onchange result
        :rtype: dict
        """
        #play onchange on sale order
        order = self._play_order_onchange(order)
        #play onchanfe on sale order line
        order_lines = []
        for line in order['order_line']:
            order_lines.append((0, 0,
                self._play_line_onchange(line[2], order_lines, order)))
        order['order_line'] = order_lines 
        return order

