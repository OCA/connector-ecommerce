# © 2013-2016 Camptocamp SA
# © 2013-2016 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Connector for E-Commerce",
    "version": "18.0.1.0.0",
    "category": "Hidden",
    "author": "Camptocamp,Akretion,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/connector-ecommerce",
    "license": "AGPL-3",
    "depends": [
        # odoo
        "stock_delivery",
        # OCA/bank-payment-alternative
        "account_payment_base_oca_sale",
        # OCA/connector
        "connector_base_product",
        # OCA/sale-workflow
        "sale_exception",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "wizard/sale_ignore_cancel_view.xml",
        "data/ecommerce_data.xml",
        "views/sale_order.xml",
        "views/account_move.xml",
        "views/stock_picking.xml",
        "views/account_journal.xml",
        "views/account_payment_method_line.xml",
    ],
    "installable": True,
}
