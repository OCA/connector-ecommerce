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
 'version': '9.0.1.0.0',
 'category': 'Hidden',
 'author': "Camptocamp,Akretion,Odoo Community Association (OCA)",
 'website': 'http://openerp-connector.com',
 'license': 'AGPL-3',
 'depends': [
     'connector',
     'sale_automatic_workflow_payment_mode',
     'sale_exception',
     'delivery',
     'connector_base_product',
 ],
 'data': [
     'security/security.xml',
     'security/ir.model.access.csv',
     'wizard/sale_ignore_cancel_view.xml',
     'data/ecommerce_data.xml',
     'views/sale_view.xml',
     'views/invoice_view.xml',
     'views/stock_view.xml',
     'views/payment_mode_view.xml',
 ],
 'installable': True,
 }
