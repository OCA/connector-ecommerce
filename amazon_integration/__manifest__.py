# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Amazon Integration',
    'summary': """
        Amazon Integration""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'website': 'https://github.com/OCA/connector-ecommerce',
    'depends': ['sale_management', 'stock'],
    'category': 'Sales',
    'author': 'Domatix, '
              'Odoo Community Association (OCA)',
    'external_dependencies': {
        'python': [
            'mws',
        ],
    },
    'data': ['security/ir.model.access.csv',
             'data/ir_cron.xml',
             'data/product_data.xml',
             'views/amazon_marketplace.xml',
             'views/amazon_seller.xml',
             'views/res_config_settings.xml',
             'views/amazon_menuitems.xml',
             'views/sale_order.xml',
             ],
    'development_status': 'Alpha',
    'installable': True,
}
