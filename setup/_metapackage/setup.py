import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-connector-ecommerce",
    description="Meta package for oca-connector-ecommerce Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-connector_ecommerce',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
