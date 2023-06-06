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
    'name': 'Academy facility management',
    'summary': 'Academy facility management Module Project',
    'version': '1.0',

    'description': """
Academy facility management Module Project.
==============================================


    """,

    'author': 'Jorge Soto Garcia',
    'maintainer': 'Jorge Soto Garcia',
    'contributors': ['Jorge Soto Garcia <sotogarcia@gmail.com>'],

    'website': 'http://www.gitlab.com/sotogarcia',

    'license': 'AGPL-3',
    'category': 'Academy',

    'depends': [
        'base',
        'academy_base',
        'facility_management',
        'base_field_m2m_view'
    ],

    'data': [
        'security/academy_training_action_facility_link.xml',
        'views/academy_training_action_facility_link_view.xml',
        'views/academy_competency_unit_view.xml',
        'views/academy_training_action_view.xml'
    ],

    'installable': True,
    'auto_install': True
}
