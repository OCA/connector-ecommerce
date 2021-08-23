# -*- coding: utf-8 -*-
# © 2013-TODAY Akretion (Sébastien Beau)
# © 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component


class OnChangeManager(Component):

    _name = 'ecommerce.onchange.manager'
    _inherit = 'base.connector'

    def get_new_values(self, record, on_change_result, model=None):
        vals = on_change_result.get('value', {})
        new_values = {}
        for fieldname, value in vals.iteritems():
            if fieldname not in record:
                if model:
                    column = self.env[model]._fields[fieldname]
                    if column.type == 'many2one' and value is not False:
                        value = value[0]   # many2one are tuple (id, name)
                new_values[fieldname] = value
        return new_values

    def play_onchanges(self, model, values, onchange_fields):
        model = self.env[model]
        onchange_specs = model._onchange_spec()

        # we need all fields in the dict even the empty ones
        # otherwise 'onchange()' will not apply changes to them
        all_values = values.copy()
        for field in model._fields:
            if field not in all_values:
                all_values[field] = False

        # we work on a temporary record
        new_record = model.new(all_values)

        new_values = {}
        for field in onchange_fields:
            onchange_values = new_record.onchange(all_values,
                                                  field, onchange_specs)
            new_values.update(self.get_new_values(values, onchange_values,
                                                  model=model._name))
            all_values.update(new_values)

        res = {f: v for f, v in all_values.iteritems()
               if f in values or f in new_values}
        return res


class SaleOrderOnChange(Component):

    _name = 'ecommerce.onchange.manager.sale.order'
    _inherit = 'ecommerce.onchange.manager'
    _usage = 'ecommerce.onchange.manager.sale.order'

    order_onchange_fields = [
        'partner_id',
        'partner_shipping_id',
        'payment_mode_id',
        'workflow_process_id',
    ]

    line_onchange_fields = [
        'product_id',
    ]

    def play(self, order, order_lines):
        """ Play the onchange of the sales order and it's lines

        :param order: sales order values
        :type: dict
        :param order_lines: data of the sales order lines
        :type: list of dict

        :return: the sales order updated by the onchanges
        :rtype: dict
        """
        # play onchange on sales order
        order = self.play_onchanges('sale.order', order,
                                    self.order_onchange_fields)

        # play onchange on sales order line
        processed_order_lines = []
        line_lists = [order_lines]
        if 'order_line' in order and order['order_line'] is not order_lines:
            # we have both backend-dependent and oerp-native order
            # lines.
            # oerp-native lines can have been added to map
            # shipping fees with an Odoo Product
            line_lists.append(order['order_line'])

        for line_list in line_lists:
            for idx, command_line in enumerate(line_list):
                # line_list format:[(0, 0, {...}), (0, 0, {...})]
                if command_line[0] in (0, 1):  # create or update values
                    # keeps command number and ID (or 0)
                    old_line_data = command_line[2]
                    new_line_data = self.play_onchanges(
                        'sale.order.line',
                        old_line_data,
                        self.line_onchange_fields
                    )
                    new_line = (command_line[0],
                                command_line[1],
                                new_line_data)
                    processed_order_lines.append(new_line)
                    # in place modification of the sales order line in the list
                    line_list[idx] = new_line
        return order
