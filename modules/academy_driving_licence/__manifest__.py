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
    "name": "Academy Driving Licenses",
    "summary": "Connect students with driving licenses",
    "version": "1.0",
    "description": "Connect students with driving licenses",
    "author": "Jorge Soto Garcia",
    "maintainer": "Jorge Soto Garcia",
    "contributors": ["Jorge Soto Garcia <sotogarcia@gmail.com>"],
    "website": "https://www.github.com/sotogarcia",
    "license": "AGPL-3",
    "category": "Academy",
    "depends": ["base", "academy_base", "driving_licence"],
    "data": ["views/academy_student_view.xml"],
    "installable": True,
    "auto_install": True,
}
