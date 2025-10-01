# -*- coding: utf-8 -*-
###############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) All rights reserved:
#        (c) Jorge Soto Garcia, 2025
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
    "name": "Academy facility management",
    "summary": "Academy facility management Module Project",
    "version": "18.0.1.0.0",
    "description": """
Bridge module connecting the academic framework with the facility management
system, enabling reservations and usage tracking of rooms, labs and equipment
from within training actions.

Key features:

- Facility linking: associate training actions and enrolments with specific rooms,
  labs, equipment and other resources.
- Reservation integration: synchronize academic schedules with facility
  reservations to avoid conflicts and double-bookings.
- Scheduler support: view and manage reservations through timeline and
  calendar interfaces.
- Batch operations: reserve or release facilities for multiple actions via wizard.
- Data consistency: ensures that academic activities (programs, actions,
  enrolments) are aligned with facility availability and capacity.
- Security rules: access control for facility usage within the academy context.

This module does not add standalone features but acts as a connector, ensuring
that the academic workflows in `academy_base` are fully integrated with the
facility catalog and reservation engine provided by `facility_management`.
    """,
    "author": "Jorge Soto Garcia",
    "maintainer": "Jorge Soto Garcia",
    "contributors": ["Jorge Soto Garcia <sotogarcia@gmail.com>"],
    "website": "https://www.github.com/sotogarcia",
    "license": "AGPL-3",
    "category": "Academy",
    "depends": [
        "base",
        "academy_base",
        "facility_management",
        "base_field_m2m_view",
    ],
    "data": [
        "security/academy_training_action_facility_link.xml",
        "security/facility_reservation.xml",
        "views/academy_training_action_facility_link_view.xml",
        "views/academy_training_action_view.xml",
        "views/academy_training_action_enrolment_view.xml",
        "views/facility_reservation_scheduler_view.xml",
        "views/facility_reservation_view.xml",
    ],
    "installable": True,
    "auto_install": True,
}
