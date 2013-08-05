# -*- coding: utf-8 -*-
##############################################################################
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
##############################################################################

from openerp.addons.connector.connector import ConnectorUnit


class OnChangeManager(ConnectorUnit):
    def merge_values(self, record, on_change_result):
        vals = on_change_result.get('value', {})
        for key in vals:
            if not key in record:
                record[key] = vals[key]


class SaleOrderOnChange(OnChangeManager):
    _model_name = None

    def _get_partner_id_onchange_param(self, order):
        """ Prepare the arguments for calling the partner_id change
        on sale order. You can overwrite this method in your own
        module if they modify the onchange signature

        :param order: a dictionary of the value of your sale order
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

    def _get_shop_id_onchange_param(self, order):
        args = [None,
                order['shop_id']]
        kwargs = {'context': self.session.context}
        return args, kwargs

    def _get_payment_method_id_onchange_param(self, order):
        args = [None,
                order['payment_method_id']]
        kwargs = {'context': self.session.context}
        return args, kwargs

    def _get_workflow_process_id_onchange_param(self, order):
        args = [None,
                order['workflow_process_id']]
        kwargs = {'context': self.session.context}
        return args, kwargs

    def _play_order_onchange(self, order):
        """ Play the onchange of the sale order

        :param order: a dictionary of the value of your sale order
        :type: dict

        :return: the value of the sale order updated with the onchange result
        :rtype: dict
        """
        sale_model = self.session.pool.get('sale.order')

        #Play partner_id onchange
        args, kwargs = self._get_shop_id_onchange_param(order)
        res = sale_model.onchange_shop_id(self.session.cr,
                                          self.session.uid,
                                          *args,
                                          **kwargs)
        self.merge_values(order, res)

        args, kwargs = self._get_partner_id_onchange_param(order)
        res = sale_model.onchange_partner_id(self.session.cr,
                                             self.session.uid,
                                             *args,
                                             **kwargs)
        self.merge_values(order, res)

        if order.get('payment_method_id'):
            # apply payment method
            args, kwargs = self._get_payment_method_id_onchange_param(order)
            res = sale_model.onchange_payment_method_id(self.session.cr,
                                                        self.session.uid,
                                                        *args,
                                                        **kwargs)
        self.merge_values(order, res)

        if order.get('workflow_process_id'):
            # apply default values from the workflow
            args, kwargs = self._get_workflow_process_id_onchange_param(order)
            res = sale_model.onchange_workflow_process_id(self.session.cr,
                                                        self.session.uid,
                                                        *args,
                                                        **kwargs)
        self.merge_values(order, res)
        return order

    def _get_product_id_onchange_param(self, line, previous_lines, order):
        """ Prepare the arguments for calling the product_id change
        on sale order line. You can overwrite this method in your own
        module if they modify the onchange signature

        :param line: the sale order line to process
        :type: dict
        :param previous_lines: list of dict of the previous lines processed
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
        uos_qty = float(line.get('product_uos_qty', 0))
        if not uos_qty:
            uos_qty = float(line.get('product_uom_qty', 0))

        kwargs ={
            'qty': float(line.get('product_uom_qty', 0)),
            'uom': line.get('product_uom'),
            'qty_uos': uos_qty,
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

    def _play_line_onchange(self, line, previous_lines, order):
        """ Play the onchange of the sale order line

        :param line: the sale order line to process
        :type: dict
        :param previous_lines: list of dict of the previous line processed
        :type: list
        :param order: data of the sale order
        :type: dict

        :return: the value of the sale order updated with the onchange result
        :rtype: dict
        """
        sale_line_model = self.session.pool.get('sale.order.line')

        #Play product_id onchange
        args, kwargs = self._get_product_id_onchange_param(line,
                                                           previous_lines,
                                                           order)
        res = sale_line_model.product_id_change(self.session.cr,
                                                self.session.uid,
                                                *args,
                                                **kwargs)
        # TODO refactor this with merge_values
        vals = res.get('value', {})
        for key in vals:
            if not key in line:
                if sale_line_model._columns[key]._type == 'many2many':
                    line[key] = [(6, 0, vals[key])]
                else:
                    line[key] = vals[key]
        return line

    def play(self, order, order_lines):
        """ Play the onchange of the sale order and it's lines

        :param order: data of the sale order
        :type: dict

        :return: the value of the sale order updated with the onchange result
        :rtype: dict
        """
        #play onchange on sale order
        with self.session.change_context(dict(shop_id=order.get('shop_id'))):
            order = self._play_order_onchange(order)
        #play onchanfe on sale order line
        processed_order_lines = []
        line_lists = [order_lines]
        if 'order_line' in order and order['order_line'] is not order_lines:
            # we have both backend-dependent and oerp-native order
            # lines.
            # oerp-native lines can have been added to map
            # shipping fees with an OpenERP Product
            line_lists.append(order['order_line'])
        for line_list in line_lists:
            for idx, command_line in enumerate(line_list):
                # line_list format:[(0, 0, {...}), (0, 0, {...})]
                if command_line[0] in (0, 1):  # create or update values
                    # keeps command number and ID (or 0)
                    old_line_data = command_line[2]
                    new_line_data = self._play_line_onchange(
                        old_line_data, processed_order_lines, order)
                    new_line = (command_line[0], command_line[1], new_line_data)
                    processed_order_lines.append(new_line)
                    # in place modification of the sale order line in the list
                    line_list[idx] = new_line
        return order
