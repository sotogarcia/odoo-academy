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
    "name": "Academy Base",
    "summary": """
        Common information and behavior used by the academy modules""",
    "description": """
The Academy Base module provides the foundation for managing training offers
within the Spanish Vocational Training System. It implements common structures,
data models and behaviors shared across academy modules.

Key features:

- Defines and manages the main reference catalogs aligned with the Spanish
  National Catalogue of Professional Qualifications and Training Offers (LO 3/2022
  and RD 659/2023):
  • Application scopes
  • Training methodologies and modalities
  • Knowledge areas
  • Professional families, fields, sectors and categories
  • Competency units (ECP) and training modules
  • Qualification levels and educational attainment
  • Professional qualifications
  • Training frameworks (Grades A, B, C, D, E)

- Supports core training entities:
  • Training programs and program lines
  • Training actions and action lines
  • Enrolments, students, teachers, technical and support staff

- Provides demo data, initial sequences, groups, wizards and security rules.

This module is required as a dependency for any specialized academy modules
(e.g. quality surveys, planning, certifications), ensuring consistency in the use
of reference catalogs and training structures across the platform.
    """,
    "author": "Jorge Soto Garcia",
    "website": "https://github.com/sotogarcia",
    "category": "Academy",
    "version": "18.0.1.0.0",
    "depends": [
        "base",
        "mail",
        "record_ownership",
        "base_field_m2m_view",
        "partner_firstname",
        "cefrl",
    ],
    "data": [
        "data/res_partner_category_data.xml",
        # "data/academy_teacher_data.xml",
        "data/mail_message_subtype_data.xml",
        "data/res_groups_data.xml",
        "data/ir_sequence_data.xml",
        "data/ir_actions_server_data.xml",
        "data/academy_training_methodology_data.xml",
        "data/academy_training_modality_data.xml",
        "data/academy_application_scope_data.xml",
        "data/academy_knowledge_area_data.xml",
        "data/academy_qualification_level_data.xml",
        "data/academy_educational_attainment_data.xml",
        "data/academy_professional_family_data.xml",
        "data/academy_professional_field_data.xml",
        "data/academy_professional_sector_data.xml",
        "data/res_partner_data.xml",
        "data/academy_student_data.xml",
        "data/academy_training_framework_data.xml",
        "data/ir_cron_data.xml",
        "security/academy_base.xml",
        "security/academy_training_framework.xml",
        "security/academy_training_methodology.xml",
        "security/academy_application_scope.xml",
        "security/academy_knowledge_area.xml",
        "security/academy_professional_area.xml",
        "security/academy_training_modality.xml",
        "security/academy_competency_unit.xml",
        "security/academy_qualification_level.xml",
        "security/academy_educational_attainment.xml",
        "security/academy_professional_category.xml",
        "security/academy_professional_family.xml",
        "security/academy_professional_qualification.xml",
        "security/academy_professional_field.xml",
        "security/academy_professional_sector.xml",
        "security/academy_training_module.xml",
        "security/academy_training_program.xml",
        "security/academy_training_action.xml",
        "security/academy_training_action_enrolment.xml",
        "security/academy_support_staff.xml",
        "security/academy_technical_staff.xml",
        "security/academy_teacher.xml",
        "security/academy_student.xml",
        "security/academy_training_action_enrolment_wizard.xml",
        "security/academy_student_wizard.xml",
        "security/academy_training_program_line.xml",
        "security/academy_training_action_line.xml",
        "security/academy_training_action_group.xml",
        "views/academy_base.xml",
        "views/academy_training_framework_view.xml",
        "views/academy_training_methodology_view.xml",
        "views/academy_application_scope_view.xml",
        "views/academy_knowledge_area_view.xml",
        "views/academy_professional_area_view.xml",
        "views/academy_training_modality_view.xml",
        "views/academy_qualification_level_view.xml",
        "views/academy_educational_attainment_view.xml",
        "views/academy_professional_category_view.xml",
        "views/academy_professional_family_view.xml",
        "views/academy_professional_qualification_view.xml",
        "views/academy_professional_field_view.xml",
        "views/academy_professional_sector_view.xml",
        "views/academy_training_module_view.xml",
        "views/academy_competency_unit_view.xml",
        "views/academy_training_program_view.xml",
        "views/academy_training_action_view.xml",
        "views/academy_training_action_enrolment_view.xml",
        "views/academy_support_staff_view.xml",
        "views/academy_technical_staff.xml",
        "views/academy_student_view.xml",
        "views/academy_teacher_view.xml",
        "views/academy_training_program_line_view.xml",
        "views/academy_training_action_line_view.xml",
        "views/academy_training_action_group_view.xml",
        "views/res_config_settings_view.xml",
        "report/academy_training_program_details_report.xml",
        "wizard/academy_student_wizard_view.xml",
        "wizard/academy_training_action_enrolment_wizard_view.xml",
        "wizard/record_ownership_wizard_view.xml",
    ],
    "pre_init_hook": "pre_init_hook",
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "qweb": [],
    "demo": [
        "demo/academy_student_demo.xml",
        "demo/res_partner.xml",
        "demo/res_company_demo.xml",
        "demo/res_users.xml",
        "demo/academy_teacher_demo.xml",
        "demo/academy_professional_area.xml",
        "demo/academy_professional_category.xml",
        "demo/academy_professional_qualification.xml",
        "demo/academy_training_module.xml",
        "demo/academy_training_program.xml",
        "demo/academy_competency_unit.xml",
        "demo/academy_training_action.xml",
        "demo/ir_atachment.xml",
        "demo/academy_training_action_enrolment_demo.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "academy_base/static/src/css/academy_base_view.css",
            "academy_base/static/src/css/academy_training_program_details_report.css",
            "academy_base/static/src/scss/academy_program.scss",
        ],
        "web.report_assets_common": [
            "academy_base/static/src/css/academy_training_program_details_report.css",
        ],
        "web.report_assets_pdf": [
            "academy_base/static/src/css/academy_training_program_details_report.css",
        ],
    },
    "external_dependencies": {"python": []},
    "license": "AGPL-3",
}
