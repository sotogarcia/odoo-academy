###############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) All rights reserved:
#        (c) 2015  Jorge Soto Garcia
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

{  # noqa: B018
    "name": "Academic Profile",
    "version": "18.0.1.0.0",
    "summary": (
        "Integrate language qualifications, driving licences, and "
        "educational classifications into academy student profiles"
    ),
    "description": """
Academic Profile
================

This module integrates educational and professional qualification
information into the academy student profile.

It connects the academy management system with standard reference
catalogues for languages, driving licences, and educational
classifications.

Key Features
------------

The module is designed to support:

- Language qualifications based on the Common European Framework of
  Reference for Languages (CEFR).
- Driving licences and their corresponding categories.
- Educational classifications based on international and national
  classification systems, including ISCED.
- Integration of these references with academy student records.

Integration
-----------

The module extends academy_base through integration with:

- cefrl: Language proficiency levels and certificates.
- driving_licence: Driving licence categories.
- education_classification: Educational classification schemes,
  editions, categories, and correspondence mappings.

Intended Audience
-----------------

Educational institutions, vocational training centres, and training
providers that need to manage students' educational backgrounds,
language qualifications, and professional credentials.

Benefits
--------

- Centralize academic and professional qualification information.
- Reuse standardized reference catalogues.
- Facilitate searching and classification of student profiles.
- Keep additional qualification management separate from the
  core academy_base module.
""",
    "author": "Jorge Soto Garcia",
    "website": "https://github.com/academia-postal-3/odoo-academy",
    "license": "AGPL-3",
    "category": "Academy",
    "maintainer": "Jorge Soto Garcia",
    "contributors": ["Jorge Soto Garcia <sotogarcia@gmail.com>"],
    "depends": [
        "academy_base",
        "cefrl",
        "driving_licence",
        "education_classification",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/academy_academic_training_view.xml",
        "views/academy_support_staff_view.xml",
    ],
    "demo": [],
    "application": False,
    "installable": True,
    "auto_install": False,
}
