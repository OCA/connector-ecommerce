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
 'version': '2.0.0',
 'category': 'Connector',
 'author': 'MagentoERPConnect Core Editors',
 'website': 'http://www.magentoerpconnect.com',
 'license': 'AGPL-3',
 'description': """
Connector for E-Commerce
========================

TODO
----

Review the description

Old Description
---------------

This module provide an abstract common minimal base to multi-channels sales.
Say you want to expose your product catalog to
* several instances of flashy-sluggish Magento web sites
* a cutting edge Spree web shop
* a Neteven online Marketplace
* EBay
* Amazon
* Google Base
* an external Point Of Sale system
* ...
Then this module allows you to:
* use several external references ids on every OpenERP object matching those all those external referentials
* per referential instance, use several sale sub platform entities (ex: several Magento websites per instance)
* per sub platform, use several shops (ex: several Magento web shops per website)

For each sale shop (matching OpenERP sale.shop object), this module abstract the interfaces to:
* export the catalog, shop warehouse stock level wise, shop pricelist wise
* import the catalog
* import orders
* export orders/picking status
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
     'sale_view.xml',
     'product_view.xml',
     'invoice_view.xml',
     'ecommerce_data.xml',
     # 'settings/sale.exception.csv',  # TODO reimplement the check
     'stock_view.xml',
     'payment_method_view.xml',
     'account_view.xml',
 ],
 'installable': True,
}
