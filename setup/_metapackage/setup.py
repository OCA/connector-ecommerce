import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo9-addons-oca-connector-ecommerce",
    description="Meta package for oca-connector-ecommerce Odoo addons",
    version=version,
    install_requires=[
        'odoo9-addon-connector_ecommerce',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
