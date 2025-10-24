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
    "name": "Academy Timesheets",
    "summary": """
        Manage the schedules of classes, students and teachers""",
    "description": """
Plan, organize and monitor all academy schedules: training sessions, teachers,
students and facility usage.

Key features:

- Session scheduling: create and manage training sessions with dates, times,
  facilities and assigned teachers.
- Timetable generation: build and print schedules for students, teachers,
  training actions and facilities.
- Conflict detection: prevent overlaps in teacher allocation, student enrolments,
  and facility reservations.
- Affinities & invitations: manage session invitations, teacher affinities, and
  operational shifts.
- Non-teaching tasks: register and schedule meetings, support duties and other
  tasks beyond teaching hours.
- Wizards & automation:

  - Clone sessions or full timetables across periods.
  - Verification tools for timetable consistency.
  - Search and allocate available teachers automatically.
  - Send schedules by email and download/export in multiple formats.
- Reports: generate structured timetables per student, teacher, training action or
  primary instructor, with customizable layouts.
- Integration:

  - Extends academy_base and facility_management to ensure consistency
    between sessions, enrolments and reservations.
  - Links with record ownership for access control and audit trails.
- UI/UX: custom widgets, header buttons, calendar/list/kanban views, and CSS
  styles for printed and digital reports.

This module provides a complete timetable management solution for academies,
ensuring reliable scheduling and smooth coordination between students, teachers,
training actions and facilities.
    """,
    "author": "Jorge Soto Garcia",
    "website": "https://github.com/sotogarcia",
    "category": "Academy",
    "version": "18.0.1.0.0",
    "depends": [
        "academy_base",
        "base_field_m2m_view",
        "facility_management",
        "record_ownership",
    ],
    # 'pre_init_hook': 'pre_init_hook',
    # 'post_init_hook': 'post_init_hook',
    # 'uninstall_hook': 'uninstall_hook',
    "data": [
        "views/academy_timesheets.xml",
        "data/ir_actions_server_data.xml",
        "data/html_templates_data.xml",
        "data/report_paperformat_data.xml",
        "data/mail_message_subtype_data.xml",
        "data/mail_notification_email_data.xml",
        "security/academy_training_session.xml",
        "security/academy_training_session_invitation.xml",
        "security/academy_training_session_teacher_assignment.xml",
        "security/academy_timesheets_clone_wizard_log.xml",
        "security/academy_teacher_operational_shift.xml",
        "views/academy_training_session_view.xml",
        "views/academy_training_session_invitation_view.xml",
        "views/academy_training_action_line_view.xml",
        "views/academy_teacher_view.xml",
        "views/academy_training_action_view.xml",
        "views/academy_student_view.xml",
        "views/facility_reservation_view.xml",
        "views/academy_training_session_teacher_assignment_view.xml",
        "views/academy_training_action_enrolment_view.xml",
        "views/academy_timesheets_clone_wizard_log_view.xml",
        "views/academy_teacher_operational_shift_view.xml",
        "views/res_config_settings_view.xml",
        # "wizard/academy_timesheets_send_by_mail_wizard_view.xml",
        # "wizard/academy_timesheets_session_state_wizard_view.xml",
        # "wizard/academy_timesheets_download_wizard_view.xml",
        # "wizard/academy_timesheets_clone_wizard_view.xml",
        # "wizard/academy_timesheets_verification_wizard_view.xml",
        # "wizard/academy_timesheets_search_teachers_wizard_view.xml",
        "report/academy_timesheet_layout_report.xml",
        "report/academy_timesheet_primary_instructor_report.xml",
        "report/academy_timesheet_training_action_report.xml",
        "report/academy_timesheet_student_report.xml",
        "data/mail_template_data.xml",  # It should be included after reports
    ],
    "assets": {
        "web.assets_backend": [
            "/academy_timesheets/static/src/css/academy_timesheets.css",
            "/academy_timesheets/static/src/js/academy_timesheets_ready_draft_field.esm.js",
            "/academy_timesheets/static/src/xml/academy_timesheets_ready_draft_field.xml",
            # "/academy_timesheets/static/src/js/header_view_buttons.js",
            # "/academy_timesheets/static/src/xml/header_view_buttons.xml",
        ],
        "web.report_assets_common": [
            "/academy_timesheets/static/src/css/academy_timesheets_report.css",
        ],
        "web.report_assets_pdf": [
            "/academy_timesheets/static/src/css/academy_timesheets_report.css",
        ],
    },
    "demo": [
        "demo/facility_facility_demo.xml",
        "demo/academy_training_action_demo.xml",
        "demo/facility_facility_reservation_demo.xml",
        "demo/academy_training_session_demo.xml",
        "demo/academy_training_session_teacher_assignment_demo.xml",
    ],
    "external_dependencies": {"python": []},
    "license": "AGPL-3",
}
