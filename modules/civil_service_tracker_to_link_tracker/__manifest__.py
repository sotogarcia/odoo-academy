# -*- coding: utf-8 -*-
###############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) All rights reserved:
#        (c) 2025 Jorge Soto Garcia
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
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

{
    'name': 'Civil Service Tracker - Link tracker Integration',
    'summary': 'Link civil service processes with link tracker',
    'version': '13.0.1.0.0',
    'description': """
Civil Service Tracker - Link tracker Integration
=================================================

This module integrates civil_service_tracker with link_tracker,
allowing civil service processes to be associated with external resources
such as official bulletins, announcements, and institutional websites.
    """,
    'author': 'Jorge Soto Garcia',
    'maintainer': 'Jorge Soto Garcia',
    'contributors': [
        'Jorge Soto Garcia <sotogarcia@gmail.com>',
    ],
    'website': 'https://gitlab.com/sotogarcia',
    'license': 'AGPL-3',
    'category': 'Human Resources/Public Sector',
    'depends': [
        'civil_service_tracker',
        'link_tracker',
    ],
    'external_dependencies': {
        'python': [],
    },
    'data': [
        'data/utm_campaign_data.xml',
        'data/utm_source_data.xml',
        'data/link_tracker_data.xml',

        'views/link_tracker_view.xml',
    ],
    'assets': {},
    'images': [],
    'installable': True,
    'application': False,
    'auto_install': True
}
