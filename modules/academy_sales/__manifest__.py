# -*- coding: utf-8 -*-
{
    'name': "Academy Sales",

    'summary': """
        Links academy base to sales module""",

    'description': """
        All the required components and behavior to sell training actions and
        training modules as service and as product.
    """,

    'author': "Jorge Soto Garcia",
    'website': "https://github.com/sotogarcia",

    'category': 'Academy',
    'version': '13.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'mail',
        'academy_base',
        'uom',
        'product',
        'sale_management'
    ],

    # always loaded
    'data': [
        'views/academy_sales.xml',

        'data/product_category_data.xml',
        'data/uom_uom_data.xml',
        'data/product_product_data.xml',

        'views/academy_training_action_enrolment_view.xml',
        'views/academy_training_action_view.xml',
        'views/academy_training_module_view.xml',
    ],
    'qweb': [

    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'js': [
    ],
    'css': [
    ],
    "external_dependencies": {
        "python": []
    },
    'license': 'AGPL-3'
}
