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
    "name": "Academy Timesheets to Calendar",
    "summary": "Allow to convert timesheet sessions to calendar events",
    "description": "Allow to convert timesheet sessions to calendar events",
    "category": "Academy",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "author": "Jorge Soto Garcia",
    "maintainer": "Jorge Soto Garcia",
    "contributors": ["Jorge Soto Garcia <sotogarcia@gmail.com>"],
    "website": "https://www.github.com/sotogarcia",
    "depends": ["base", "calendar", "academy_timesheets"],
    "external_dependencies": {
        "python": [],
    },
    "data": [
        "data/calendar_event_type_data.xml",
        "views/academy_timesheets_to_calendar.xml",
        "views/academy_training_session_view.xml",
        "views/calendar_event_view.xml",
    ],
    "demo": [],
    "js": ["static/src/js/header_view_buttons.js"],
    "css": [],
    "qweb": ["static/src/xml/header_view_buttons.xml"],
    "images": [],
    "test": [],
    "installable": True,
}
