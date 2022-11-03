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
    'summary': '''Provides several spanish administrations data and allows to
    use a singular type of regions typical of the Spanish state.
    ''',

    'author': "Jorge Soto Garcia",
    'website': "https://github.com/sotogarcia",

    'license': 'LGPL-3',
    'category': 'Technical Settings',
    'version': '15.0.1.3',

    'depends': [
        'base',
        'civil_service_recruitment'
    ],

    'data': [

        'data/res_country_region_data.xml',
        'data/res_country_state_data.xml',
        'data/res_partner_data.xml',
        'data/civil_service_recruitment_public_administration_type_data.xml',
        'data/civil_service_recruitment_public_administration_data.xml',
        'data/ir_filters.xml',

        'security/res_country_region_data.xml',

        'views/res_country_region_data_view.xml',
    ],

}
