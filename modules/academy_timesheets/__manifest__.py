# -*- coding: utf-8 -*-
{
    'name': 'Academy Timesheets',

    'summary': '''
        Manage the schedules of classes, students and teachers''',

    'description': '''
        Manage the schedules of classes, students and teachers
    ''',

    'author': 'Jorge Soto Garcia',
    'website': 'https://github.com/sotogarcia',

    'category': 'Academy',
    'version': '13.0.1.0.0',

    'depends': [
        'academy_base',
        'base_field_m2m_view',
        'facility_management',
        'record_ownership'
    ],

    'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',

    'data': [
        'views/academy_timesheets.xml',

        'data/ir_actions_server_data.xml',
        'data/html_templates_data.xml',
        'data/report_paperformat_data.xml',

        'security/academy_non_teaching_task.xml',
        'security/academy_training_session.xml',
        'security/academy_training_session_invitation.xml',
        'security/academy_training_session_affinity.xml',
        'security/academy_training_session_teacher_rel.xml',
        'security/academy_timesheets_clone_wizard_log.xml',

        'views/academy_training_session_view.xml',
        'views/academy_training_session_invitation_view.xml',
        'views/academy_training_session_affinity_view.xml',

        'views/academy_non_teaching_task_view.xml',
        'views/academy_competency_unit_view.xml',
        'views/academy_teacher_view.xml',
        'views/academy_training_action_view.xml',
        'views/academy_student_view.xml',
        'views/facility_reservation_view.xml',
        'views/academy_training_session_teacher_rel_view.xml',
        'views/academy_training_action_enrolment_view.xml',
        'views/academy_timesheets_clone_wizard_log_view.xml',
        'views/res_config_settings_view.xml',

        'wizard/academy_timesheets_send_by_mail_wizard_view.xml',
        'wizard/academy_timesheets_session_state_wizard_view.xml',
        'wizard/academy_timesheets_download_wizard_view.xml',
        'wizard/academy_timesheets_clone_wizard_view.xml',
        'wizard/academy_timesheets_verification_wizard_view.xml',

        'report/academy_timesheet_layout_report.xml',
        'report/academy_timesheet_primary_instructor_report.xml',
        'report/academy_timesheet_training_action_report.xml',
        'report/academy_timesheet_student_report.xml',

        'data/mail_template_data.xml'  # It should be included after reports
    ],

    'demo': [
        'demo/academy_training_action_demo.xml',
        'demo/facility_facility_reservation_demo.xml',
        'demo/academy_training_session_demo.xml',
        'demo/academy_training_session_teacher_rel_demo.xml'
    ],

    'js': [
        'static/src/js/academy_timesheets_widgets.js'
    ],

    'css': [
        'static/src/css/academy_timesheets.css',
        'static/src/css/academy_timesheets_report.css',
    ],

    'qweb': [
        'static/src/xml/academy_timesheets_widgets.xml'
    ],

    "external_dependencies": {
        "python": []
    },

    'license': 'AGPL-3'
}
