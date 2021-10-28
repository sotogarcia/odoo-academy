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
    'name': 'Adaptation to the Spanish Administrations',
    'summary': 'Adaptation to the Spanish Administrations Module Project',
    'version': '13.0.1.0.0',

    'description': "Adaptation to the Spanish Administrations Module Project",

    'author': 'Jorge Soto Garcia',
    'maintainer': 'Jorge Soto Garcia',
    'contributors': [' <sotogarcia@gmail.com>'],

    'website': 'http://www.gitlab.com/',

    'license': 'AGPL-3',
    'category': 'Academy',

    'depends': [
        'base',
        'academy_base',
        'academy_public_tendering'
    ],
    'external_dependencies': {
        'python': [],
    },
    'data': [
        'data/academy_public_tendering_autonomous_community_data.xml',
        'data/res_country_state_data.xml',
        'data/res_partner_data.xml',
        'data/academy_public_tendering_public_administration_type_data.xml',
        'data/academy_public_tendering_public_administration_data.xml',
        'data/ir_filters.xml',

        'security/academy_public_tendering_autonomous_community.xml',

        'views/academy_public_tendering_public_administration_view.xml',
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

    'installable': True
}
