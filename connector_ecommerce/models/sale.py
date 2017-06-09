# -*- coding: utf-8 -*-
# © 2011-2013 Camptocamp
# © 2010-2013 Akretion (Sébastien Beau)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, exceptions, _, osv

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    """ Add a cancellation mecanism in the sales orders

    When a sales order is canceled in a backend, the connectors can flag
    the 'canceled_in_backend' flag. It will:

    * try to automatically cancel the sales order
    * block the confirmation of the sales orders using a 'sales exception'

    When a sales order is canceled or the user used the button to force
    to 'keep it open', the flag 'cancellation_resolved' is set to True.

    The second axe which can be used by the connectors is the 'parent'
    sales order. When a sales order has a parent sales order (logic to
    link with the parent to be defined by each connector), it will be
    blocked until the cancellation of the sales order is resolved.

    This is used by, for instance, the magento connector, when one
    modifies a sales order, Magento cancels it and create a new one with
    the first one as parent.
    """
    _inherit = 'sale.order'

    canceled_in_backend = fields.Boolean(string='Canceled in backend',
                                         readonly=True,
                                         copy=False)
    # set to True when the cancellation from the backend is
    # resolved, either because the SO has been canceled or
    # because the user manually chose to keep it open
    cancellation_resolved = fields.Boolean(string='Cancellation from the '
                                                  'backend resolved',
                                           copy=False)
    parent_id = fields.Many2one(comodel_name='sale.order',
                                compute='_compute_parent_id',
                                string='Parent Order',
                                help='A parent sales order is a sales '
                                     'order replaced by this one.')
    need_cancel = fields.Boolean(compute='_compute_need_cancel',
                                 string='Need to be canceled',
                                 copy=False,
                                 help='Has been canceled on the backend'
                                      ', need to be canceled.')
    parent_need_cancel = fields.Boolean(
        compute='_compute_parent_need_cancel',
        string='A parent sales order needs cancel',
        help='A parent sales order has been canceled on the backend'
             ' and needs to be canceled.',
    )

    @api.one
    @api.depends()
    def _compute_parent_id(self):
        """ Need to be inherited in the connectors to implement the
        parent logic.

        See an implementation example in ``connector_magento``.
        """
        self.parent_id = False

    @api.one
    @api.depends('canceled_in_backend', 'cancellation_resolved')
    def _compute_need_cancel(self):
        """ Return True if the sales order need to be canceled
        (has been canceled on the Backend)
        """
        self.need_cancel = (self.canceled_in_backend and
                            not self.cancellation_resolved)

    @api.one
    @api.depends('need_cancel', 'parent_id',
                 'parent_id.need_cancel', 'parent_id.parent_need_cancel')
    def _compute_parent_need_cancel(self):
        """ Return True if at least one parent sales order need to
        be canceled (has been canceled on the backend).
        Follows all the parent sales orders.
        """
        self.parent_need_cancel = False
        order = self.parent_id
        while order:
            if order.need_cancel:
                self.parent_need_cancel = True
            order = order.parent_id

    @api.multi
    def _try_auto_cancel(self):
        """ Try to automatically cancel a sales order canceled
        in a backend.

        If it can't cancel it, does nothing.
        """
        resolution_msg = _("<p>Resolution:<ol>"
                           "<li>Cancel the linked invoices, delivery "
                           "orders, automatic payments.</li>"
                           "<li>Cancel the sales order manually.</li>"
                           "</ol></p>")
        for order in self:
            state = order.state
            if state == 'cancel':
                continue
            elif state == 'done':
                message = _('The sales order cannot be automatically '
                            'canceled because it is already in "Done" state.')
            else:
                try:
                    order.action_cancel()
                except (osv.osv.except_osv, osv.orm.except_orm,
                        exceptions.Warning):
                    # the 'cancellation_resolved' flag will stay to False
                    message = _("The sales order could not be automatically "
                                "canceled.") + resolution_msg
                else:
                    message = _("The sales order has been automatically "
                                "canceled.")
            order.message_post(body=message)

    @api.multi
    def _log_canceled_in_backend(self):
        message = _("The sales order has been canceled on the backend.")
        self.message_post(body=message)
        for order in self:
            message = _("Warning: the origin sales order %s has been canceled "
                        "on the backend.") % order.name
            for picking in order.picking_ids:
                picking.message_post(body=message)
            for invoice in order.invoice_ids:
                invoice.message_post(body=message)

    @api.model
    def create(self, values):
        order = super(SaleOrder, self).create(values)
        if values.get('canceled_in_backend'):
            order._log_canceled_in_backend()
            order._try_auto_cancel()
        return order

    @api.multi
    def write(self, values):
        result = super(SaleOrder, self).write(values)
        if values.get('canceled_in_backend'):
            self._log_canceled_in_backend()
            self._try_auto_cancel()
        return result

    @api.multi
    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        for sale in self:
            # the sales order is canceled => considered as resolved
            if (sale.canceled_in_backend and
                    not sale.cancellation_resolved):
                sale.write({'cancellation_resolved': True})
        return res

    @api.multi
    def ignore_cancellation(self, reason):
        """ Manually set the cancellation from the backend as resolved.

        The user can choose to keep the sales order active for some reason,
        it only requires to push a button to keep it alive.
        """
        message = (_("Despite the cancellation of the sales order on the "
                     "backend, it should stay open.<br/><br/>Reason: %s") %
                   reason)
        self.message_post(body=message)
        self.write({'cancellation_resolved': True})
        return True

    @api.multi
    def action_view_parent(self):
        """ Return an action to display the parent sales order """
        self.ensure_one()

        parent = self.parent_id
        if not parent:
            return

        view_xmlid = 'sale.view_order_form'
        if parent.state in ('draft', 'sent', 'cancel'):
            action_xmlid = 'sale.action_quotations'
        else:
            action_xmlid = 'sale.action_orders'

        action = self.env.ref(action_xmlid).read()[0]

        view = self.env.ref(view_xmlid)
        action['views'] = [(view.id if view else False, 'form')]
        action['res_id'] = parent.id
        return action

    def _create_delivery_line(self, carrier, price_unit):
        if self.order_line.filtered(lambda r: r.is_delivery):
            # skip if we have already a delivery line (created by
            # import of order)
            return
        else:
            return super(SaleOrder, self)._create_delivery_line(carrier,
                                                                price_unit)
