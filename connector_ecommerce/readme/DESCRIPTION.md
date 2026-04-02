This modules aims to be a common layer for the connectors dealing with
e-commerce.

It sits on top of the [connector](http://odoo-connector.com) framework
and is used by the e-commerce connectors, like
[magentoerpconnect](http://odoo-magento-connector.com) or
[prestashoperpconnect](https://github.com/OCA/connector-prestashop).

That's a technical module, which include amongst other things:

Events

> On which the connectors can subscribe listeners. The events it adds
> are:
>
> > - `on_invoice_paid(self, record)`
> > - `on_invoice_validated(self, record)`
> > - `on_invoice_validated(self, record)`
> > - `on_picking_out_done(self, record, method)` where method is
> >   'partial' or 'complete'
> > - `on_tracking_number_added(self, record)`
> > - `on_product_price_changed(self, record)`
>
> Components
>
> A piece of code which allows to play all the `onchanges` required when
> we create a sales order.
>
> Another one which allows to add special lines in imported sales orders
> such as Shipping fees, Cash on Delivery or Discounts.

Data Model

> Add structures shared for e-commerce connectors
