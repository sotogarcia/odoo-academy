# -*- coding: utf-8 -*-
{
    'name': "Academy Tests Reports",

    'summary': """
        Report designs to be used with academy tests
    """,

    'description': """
        This module provides several report designs can be used to print academy tests
    """,

    'author': 'Jorge Soto Garcia',
    'website': 'https://github.com/sotogarcia',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Academy',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'academy_base',
        'academy_tests'
    ],

    # always loaded
    'data': [
        'data/report_paperformat_data.xml',

        'views/test_report_layout.xml',

        'views/simple_report.xml',
        'views/townhall_report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [

    ],
}
