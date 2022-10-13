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
    'name': 'Academy Tests Coach',
    'summary': 'Coach bot that facilitates student learning',
    'version': '1.0',

    'description': """
Academy Tests Coach Module Project.
==============================================

Coach bot that allows you to program tasks to facilitate student learning
    """,

    'author': 'Jorge Soto Garcia',
    'maintainer': 'Jorge Soto Garcia',
    'contributors': ['Jorge Soto Garcia <sotogarcia@gmail.com>'],

    'website': 'http://www.gitlab.com/sotogarcia',

    'license': 'AGPL-3',
    'category': 'Uncategorized',

    'depends': [
        'base'
    ],
    'external_dependencies': {
        'python': [
        ],
    },
    'data': [
        'security/academy_tests_question_enrolment_statistics_helper.xml',
        'security/academy_tests_question_student_statistics_helper.xml',
        'security/academy_tests_question_training_action_statistics_helper.xml',
        'views/academy_tests_abstract_question_statistics_view.xml',
        'views/academy_tests_question_enrolment_statistics_helper_view.xml',
        'views/academy_tests_question_student_statistics_helper_view.xml',
        'views/academy_tests_question_training_action_statistics_helper_view.xml',
    ],
    'demo': [
    ],
    'js': [
    ],
    'css': [
    ],
    'qweb': [
    ],
    'images': [
    ],
    'test': [
    ],
}

