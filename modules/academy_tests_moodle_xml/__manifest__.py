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
    'name': 'Academy Tests To Moodle',
    'summary': 'Allow to export tests and questions to Moodle using XML',
    'version': '1.0',

    'author': 'Jorge Soto Garcia',
    'website': 'https://github.com/sotogarcia',

    'license': 'LGPL-3',
    'category': 'Academy',
    'version': '15.0.1.3',

    'depends': [
        'academy_tests'
    ],

    'data': [
        'views/academy_tests_question_view.xml'
    ]
}
