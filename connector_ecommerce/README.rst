.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License

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
  when we create a sales order.

  Another one which allows to add special lines in imported sales orders
  such as Shipping fees, Cash on Delivery or Discounts.

Data Model

  Add structures shared for e-commerce connectors

.. _`connector`: http://odoo-connector.com
.. _`magentoerpconnect`: http://odoo-magento-connector.com
.. _`prestashoperpconnect`: https://github.com/OCA/connector-prestashop

Installation
============

This module is a dependency for more advanced connectors. It does
nothing on its own and there is no reason to install it alone.

Credits
=======

Contributors
------------

See `contributors' list`_

.. _contributors' list: ./AUTHORS

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization
whose mission is to support the collaborative development of Odoo
features and promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
