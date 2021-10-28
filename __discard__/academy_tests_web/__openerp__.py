# -*- coding: utf-8 -*-
{
    'name': "Academy Tests Web",

    'summary': """
        Allow to publish test on the web""",

    'description': """
        Allow to publish test on the web
    """,

    'author': "Jorge Soto Garcia",
    'website': "https://github.com/sotogarcia",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Academy',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'academy_base',
        'academy_tests',
        'website',
    ],

    # always loaded
    'data': [
        'security/academy_test.xml',
        'security/academy_test_question.xml',
        'security/academy_test_answer.xml',

        'views/academy_post_tests_template.xml',
        'views/academy_post_test_template.xml',
        'views/academy_post_answers_table_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'js': [
        'static/src/js/academy_post_test_template.js',
        'static/src/js/academy_post_tests_template.js',
        'static/src/js/academy_post_answers_table_template.js'
    ],
    'css': [
        'static/src/css/academy_post_test_template.css',
        'static/src/css/academy_post_tests_template.css',
        'static/src/css/academy_post_answers_table_template.css'
    ],

    'license': 'AGPL-3'
}

