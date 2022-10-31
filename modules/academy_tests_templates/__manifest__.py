# -*- coding: utf-8 -*-
###############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) All rights reserved:
#        (c) 2015
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses
#
###############################################################################
{
    'name': 'Academy Tests Templates',
    'summary': 'Allows to use templates to make new tests',
    'version': '1.0',

    'description': """
Academy Tests Templates Module Project.
==============================================

You can create and store test templates with various criteria that allow you
to quickly make new test-type exercises.
    """,

    'author': 'Jorge Soto Garcia',
    'maintainer': 'Jorge Soto Garcia',
    'contributors': [' <soto@gmail.com>'],

    'website': "https://github.com/sotogarcia",

    'license': 'LGPL-3',
    'category': 'Academy',
    'version': '15.0.1.0.0',

    'depends': [
        'academy_tests',
        'mail',
    ],

    'data': [
        'security/academy_tests_templates.xml',

        'security/academy_tests_random_line.xml',
        'security/academy_tests_random_template.xml',
        'security/academy_tests_random_template_training_action_rel.xml',
        'security/academy_tests_random_line_categorization.xml',
        'security/academy_tests_random_template_type_wizard.xml',
        'security/academy_tests_random_wizard.xml',

        'views/academy_tests_random_line_categorization_view.xml',
        'views/academy_tests_random_line_view.xml',
        'views/academy_tests_random_template_view.xml',
        'views/academy_tests_random_template_training_action_rel_view.xml',

        'report/academy_tests_template_questions_report.xml',

        'wizard/academy_tests_random_wizard_view.xml',
        'wizard/academy_tests_random_template_type_wizard_view.xml'

    ],

    'demo': [
        'demo/academy_tests_random_template_demo.xml',
        'demo/academy_tests_random_line_demo.xml',
        'demo/academy_tests_random_line_categorization_demo.xml',
    ],

    'js': [
        "academy_tests/static/src/js/listview_button.js",
    ],

    'css': [
    ],

    'qweb': [
        "static/src/xml/listview_button.xml"
    ],

    "external_dependencies": {
        "python": ['unidecode', 'dicttoxml', 'chardet', 'python-docx']
    },

    'images': [
    ],

    'test': [
    ],

    "assets": {
        'web.assets_backend': [
            "academy_tests/static/src/js/academy_tests.js"
        ],
    },

    'installable': True
}
