# -*- coding: utf-8 -*-
{
    'name': "Academy tests GIFT",
    'summary': """
        Tests and questions in GIFT format """,
    'description': """
        Manage tests and questions in GIFT format, this format has been 
        been developed within the Moodle Community
    """,

    'author': "Jorge Soto Garcia",
    'website': "https://github.com/sotogarcia",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Academy',
    'version': '13.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['academy_base', 'academy_tests'],

    # always loaded
    'data': [
        'views/academy_tests_question_view.xml',

        'report/academy_tests_question_gift_report.xml',
        'report/academy_tests_test_gift_report.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
