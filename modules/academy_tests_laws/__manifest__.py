# -*- coding: utf-8 -*-
{
    'name': 'Academy Tests Laws',

    'summary': '''
        Allow use law articles as test question categories''',

    'description': '''
        Allow use law articles as test question categories
    ''',

    'author': 'Jorge Soto Garcia',
    'website': 'https://github.com/sotogarcia',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Academy',
    'version': '13.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': [
        'academy_base',
    ],

    # always loaded
    'data': [
        'views/academy_tests_question_view.xml',
        'views/academy_tests_topic_view.xml',
        'views/academy_tests_category_view.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'js': [
    ],
    'css': [
    ],
    'qweb': [
    ],
    "external_dependencies": {
        # 'more-itertools'
    },

    'license': 'AGPL-3'
}
