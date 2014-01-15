# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2013 Camptocamp SA
#    Copyright 2013 Akretion
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

{'name': 'Connector for E-Commerce',
 'version': '2.1.0',
 'category': 'Connector',
 'author': 'Connector Core Editors',
 'website': 'http://openerp-connector.com',
 'license': 'AGPL-3',
 'description': """
Connector for E-Commerce
========================

This modules aims to be a common layer for the connectors dealing with
e-commerce.

It sits on top of the `connector`_ framework and is used by the
e-commerce connectors, like `magentoerpconnect`_ or
`prestashoperpconnect`_.

That's a technical module, which include amongst other things:

Events

    On which the connectors can subscribe consumers
    (tracking number added, invoice paid, picking sent, ...)


ConnectorUnit

    A piece of code which allows to play all the ``onchanges`` required
    when we create a sale order.

Data Model

    Add structures shared for e-commerce connectors


 .. _`connector`: http://openerp-connector.com
.. _`magentoerpconnect`: http://openerp-magento-connector.com
.. _`prestashoperpconnect`: https://launchpad.net/prestashoperpconnect
""",
 'depends': [
     'connector',
     'sale_automatic_workflow',
     'sale_exceptions',
     'delivery',
 ],
 'data': [
     'security/security.xml',
     'security/ir.model.access.csv',
     'wizard/sale_ignore_cancel_view.xml',
     'sale_view.xml',
     'product_view.xml',
     'invoice_view.xml',
     'ecommerce_data.xml',
     'stock_view.xml',
     'payment_method_view.xml',
     'account_view.xml',
 ],
 'installable': True,
}
