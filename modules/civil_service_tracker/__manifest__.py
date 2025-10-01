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
    "name": "Civil Service Tracker",
    "summary": "Module for managing public sector exams",
    "version": "1.0",
    "description": """
Civil Service Tracker
=====================

This module provides a structured system to track and manage public sector job 
offers, selection processes, and administrative classifications in Spain, 
including scopes, authorities, corps, and positions.
    """,
    "author": "Jorge Soto Garcia",
    "maintainer": "Jorge Soto Garcia",
    "contributors": ["Jorge Soto Garcia <sotogarcia@gmail.com>"],
    "website": "https://www.github.com/sotogarcia",
    "category": "Human Resources/Public Sector",
    "license": "AGPL-3",
    "depends": [
        "base",
        "mail",
        "record_ownership",
        "attachment_effective_url",
    ],
    "external_dependencies": {
        "python": ["validators"],
    },
    "data": [
        # 'data/res_partner_data.xml',
        # 'data/civil_service_tracker_issuing_authority_data.xml',
        # 'data/civil_service_tracker_public_administration_data.xml',
        "security/res_groups.xml",
        "data/civil_service_tracker_administrative_region_data.xml",
        "data/civil_service_tracker_access_type_data.xml",
        "data/civil_service_tracker_administration_scope_data.xml",
        "data/civil_service_tracker_administration_type_data.xml",
        "data/civil_service_tracker_contract_type_data.xml",
        "data/civil_service_tracker_employment_scheme_data.xml",
        "data/civil_service_tracker_employment_group_data.xml",
        "data/civil_service_tracker_event_type_data.xml",
        "data/civil_service_tracker_selection_method_data.xml",
        "data/civil_service_tracker_vacancy_type_data.xml",
        "data/res_country_state_data.xml",
        "data/ir_exports_data.xml",
        "data/ir_actions_server_data.xml",
        "data/ir_config_parameter_data.xml",
        "data/mail_template/civil_service_tracker_events_between_dates.xml",
        "security/civil_service_tracker_administrative_region.xml",
        "security/civil_service_tracker_access_type.xml",
        "security/civil_service_tracker_public_administration.xml",
        "security/civil_service_tracker_administration_scope.xml",
        "security/civil_service_tracker_administration_type.xml",
        "security/civil_service_tracker_contract_type.xml",
        "security/civil_service_tracker_employment_scheme.xml",
        "security/civil_service_tracker_employment_group.xml",
        "security/civil_service_tracker_event_type.xml",
        "security/civil_service_tracker_issuing_authority.xml",
        "security/civil_service_tracker_process_event.xml",
        "security/civil_service_tracker_public_offer.xml",
        "security/civil_service_tracker_selection_method.xml",
        "security/civil_service_tracker_selection_process.xml",
        "security/civil_service_tracker_vacancy_position.xml",
        "security/civil_service_tracker_vacancy_type.xml",
        "security/civil_service_tracker_service_position.xml",
        "security/ir_attachment.xml",
        "views/civil_service_tracker.xml",
        "views/civil_service_tracker_administrative_region_view.xml",
        "views/civil_service_tracker_access_type_view.xml",
        "views/civil_service_tracker_administration_scope_view.xml",
        "views/civil_service_tracker_administration_type_view.xml",
        "views/civil_service_tracker_public_administration_view.xml",
        "views/civil_service_tracker_contract_type_view.xml",
        "views/civil_service_tracker_employment_scheme_view.xml",
        "views/civil_service_tracker_employment_group_view.xml",
        "views/civil_service_tracker_event_type_view.xml",
        "views/civil_service_tracker_issuing_authority_view.xml",
        "views/civil_service_tracker_process_event_view.xml",
        "views/civil_service_tracker_public_offer_view.xml",
        "views/civil_service_tracker_selection_method_view.xml",
        "views/civil_service_tracker_selection_process_view.xml",
        "views/civil_service_tracker_vacancy_position_view.xml",
        "views/civil_service_tracker_vacancy_type_view.xml",
        "views/civil_service_tracker_service_position_views.xml",
        "views/ir_attachment_view.xml",
        "views/res_config_settings_view.xml",
        "wizard/civil_service_tracker_related_partner_wizard_view.xml",
        "wizard/civil_service_tracker_quick_offer_wizard_view.xml",
        "wizard/civil_service_tracker_quick_offer_wizard_line_view.xml",
        "wizard/civil_service_tracker_events_between_dates_wizard_view.xml",
        "views/controllers/route_web_selection_process_item_view.xml",
    ],
    "demo": [],
    "js": [
        "/civil_service_tracker/static/src/js/civil-service-widget.js",
        "/civil_service_tracker/static/src/js/url_truncated_widget.js",
        "/civil_service_tracker/static/src/js/header_view_buttons.js",
        "/civil_service_tracker/static/src/js/quick_offer_form_patch.js",
    ],
    "css": ["/civil_service_tracker/static/src/css/styles-backend.css"],
    "qweb": ["static/src/xml/header_view_buttons.xml"],
    "images": [],
    "test": [],
    "installable": True,
}
