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
    'name': 'Bridge Academy-Human Resources',
    'summary': 'Integration of teachers with HR Management',
    'version': '13.0.1.0.0',

    'description': """
This Odoo module offers a robust solution for educational institutions and
training centers using Odoo to manage their human resources and academic staff
efficiently. By binding the academy.teacher model with the hr.employee model,
this module ensures a seamless and automated synchronization of data between
academic staff and HR management.
    """,

    'author': 'Jorge Soto Garcia',
    'maintainer': 'Jorge Soto Garcia',
    'contributors': [' <sotogarcia@gmail.com>'],

    'website': 'http://www.gitlab.com/sotogarcia',

    'license': 'AGPL-3',
    'category': 'Academy',

    'depends': [
        'base',
        'academy_base',
        'hr'
    ],
    'external_dependencies': {
        'python': [
        ],
    },
    'data': [
        'data/hr_department_data.xml',
        'data/hr_job_data.xml',
        'data/hr_employee_category_data.xml',

        'views/academy_teacher_view.xml'
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

    'installable': True,
    'auto_install': True
}
