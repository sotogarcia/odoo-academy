# -*- coding: utf-8 -*-
{
    'name': 'Academy Tests Templates',

    'summary': 'Allows to create, store and manage test templates',

    'author': 'Jorge Soto Garcia',
    'website': 'https://github.com/sotogarcia',

    'license': 'LGPL-3',
    'category': 'Academy',
    'version': '15.0.1.3',

    # any module necessary for this one to work correctly
    'depends': [
        'mail',
        'academy_tests'
    ],

    'data': [
        'security\academy_tests_abstract_template.xml',
        'security\academy_tests_template.xml',
        'security\academy_tests_template_categorization.xml',
        'security\academy_tests_template_line.xml',
        'security\academy_tests_template_wizard.xml',

        'views\academy_tests_abstract_template_view.xml',
        'views\academy_tests_template_categorization_view.xml',
        'views\academy_tests_template_line_view.xml',
        'views\academy_tests_template_view.xml',
    ],

    'demo': [
        'demo\academy_tests_template_categorization_demo.xml',
        'demo\academy_tests_template_line_demo.xml',
        'demo\academy_tests_template_demo.xml',
    ]

}
