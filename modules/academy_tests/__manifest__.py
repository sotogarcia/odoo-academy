# -*- coding: utf-8 -*-
{
    'name': 'Academy Tests',

    'summary': '''
        Store and manage information about tests and their questions''',

    'description': '''
        Store and manage information about tests and their questions
    ''',

    'author': 'Jorge Soto Garcia',
    'website': 'https://github.com/sotogarcia',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Academy',
    'version': '13.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': [
        'mail',
        'web',
        'web_one2many_kanban',
        'academy_base',
        'base_field_m2m_view',
        'record_ownership'
    ],

    # always loaded
    'data': [
        'data/mail_message_subtype_data.xml',
        'data/academy_tests_level_data.xml',
        'data/academy_tests_question_type_data.xml',
        'data/academy_tests_test_kind_data.xml',
        'data/academy_tests_correction_scale_data.xml',
        'data/ir_sequence.xml',
        'data/ir_cron.xml',
        'data/ir_actions_server_data.xml',
        'data/academy_tests_test_block_data.xml',

        'data/academy_tests_topic_data.xml',
        'data/academy_tests_topic_version_data.xml',
        'data/academy_tests_category_data.xml',

        'security/academy_tests.xml',
        'security/academy_tests_answer.xml',
        'security/academy_tests_answers_table.xml',
        'security/academy_tests_attempt.xml',
        'security/academy_tests_attempt_answer.xml',
        'security/academy_tests_attempt_final_answer_helper.xml',
        'security/academy_tests_category.xml',
        'security/academy_tests_correction_scale.xml',
        'security/academy_tests_level.xml',
        'security/academy_tests_question.xml',
        'security/academy_tests_question_changelog_entry.xml',
        'security/academy_tests_question_dependency_rel.xml',
        'security/academy_tests_question_duplicated_by_owner_rel.xml',
        'security/academy_tests_question_duplicated_rel.xml',
        'security/academy_tests_question_impugnment.xml',
        'security/academy_tests_question_impugnment_reply.xml',
        'security/academy_tests_question_request.xml',
        'security/academy_tests_question_request_set.xml',
        'security/academy_tests_question_training_activity_rel.xml',
        'security/academy_tests_question_training_module_rel.xml',
        'security/academy_tests_question_type.xml',
        'security/academy_tests_random_line.xml',
        'security/academy_tests_random_line_categorization.xml',
        'security/academy_tests_random_template.xml',
        'security/academy_tests_random_template_scheduled.xml',
        'security/academy_tests_random_template_training_action_rel.xml',
        'security/academy_tests_tag.xml',
        'security/academy_tests_test.xml',
        'security/academy_tests_test_block.xml',
        'security/academy_tests_test_kind.xml',
        'security/academy_tests_test_question_rel.xml',
        'security/academy_tests_test_test_block_rel.xml',
        'security/academy_tests_test_topic_rel.xml',
        'security/academy_tests_test_training_assignment.xml',
        'security/academy_tests_test_training_assignment_student_rel.xml',
        'security/academy_tests_test_training_module_helper.xml',
        'security/academy_tests_topic.xml',
        'security/academy_tests_topic_training_module_link.xml',
        'security/academy_tests_topic_training_module_link_question_rel.xml',
        'security/academy_tests_topic_version.xml',
        'security/academy_tests_uncategorized_questions_by_user.xml',
        'security/academy_tests_test_training_assignment_enrolment_rel.xml',
        'security/academy_training_module_test_category_rel.xml',
        'security/academy_training_module_test_topic_rel.xml',
        'security/ir_attachment.xml',
        'security/mail_message.xml',

        # This must be before academy_tests_tets_view.xml
        'report/academy_test_report.xml',

        'views/academy_tests.xml',
        'views/academy_tests_answer_view.xml',
        'views/academy_tests_category_view.xml',
        'views/academy_tests_level_view.xml',
        'views/academy_tests_question_impugnment_view.xml',
        'views/academy_tests_question_impugnment_reply_view.xml',
        'views/academy_tests_question_view.xml',
        'views/academy_tests_question_type_view.xml',
        'views/academy_tests_tag_view.xml',
        'views/academy_tests_test_question_rel_view.xml',
        'views/academy_tests_test_kind_view.xml',
        'views/academy_tests_tets_view.xml',
        'views/academy_tests_topic_view.xml',
        'views/ir_attachment_view.xml',
        'views/academy_tests_random_line_categorization_view.xml',
        'views/academy_tests_random_line_view.xml',
        'views/academy_tests_random_template_view.xml',
        'views/academy_tests_topic_version_view.xml',

        'views/academy_tests_topic_training_module_link_view.xml',
        'views/academy_training_module_view.xml',
        'views/academy_competency_unit_view.xml',
        'views/academy_training_action_view.xml',
        'views/academy_training_activity_view.xml',
        'views/academy_training_action_enrolment_view.xml',
        'views/academy_student_view.xml',

        'views/academy_tests_attempt_answer_view.xml',
        'views/academy_tests_attempt_view.xml',
        'views/academy_tests_correction_scale_view.xml',
        'views/academy_tests_random_template_training_action_rel_view.xml',

        'views/academy_tests_random_template_scheduled_view.xml',
        'views/academy_tests_uncategorized_by_user_readonly_view.xml',
        'views/academy_tests_question_request_view.xml',
        'views/academy_tests_question_request_set_view.xml',
        'views/academy_tests_test_block_view.xml',
        'views/academy_tests_attempt_final_answer_helper_view.xml',

        'views/academy_tests_test_training_assignment_view.xml',
        'views/academy_tests_test_training_assignment_enrolment_rel_view.xml',
        'views/res_config_settings_view.xml',

        'report/academy_tests_report_assets.xml',
        'report/academy_test_answers_table_report.xml',
        'report/academy_training_activity_details_with_topics_report.xml',
        'report/academy_statistics_student_question_readonly_report.xml',
        'report/academy_tests_uncategorized_by_user_report.xml',

        'report/academy_test_changelog_report.xml',
        'report/academy_tests_test_text_report.xml',
        'report/academy_tests_template_questions_report.xml',

        'templates/uncategorized_questions_by_user_and_topic.xml',
        'templates/duplicated_questions_by_user_and_topic.xml',
        'templates/required_questions_reminder.xml',
        'templates/verify_questions_reminder.xml',
        'templates/mail_template_you_have_impugnments.xml',
        'templates/check_training_module.xml',
        'templates/check_competency_unit.xml',
        'templates/impugnments_summary.xml',
        'templates/impugnments_summary_table_html.xml',

        'wizard/academy_tests_question_categorize_wizard_view.xml',
        'wizard/academy_tests_question_append_wizard_view.xml',
        'wizard/academy_tests_question_import_wizard_view.xml',
        'wizard/academy_tests_update_questions_wizard_view.xml',
        'wizard/academy_tests_random_wizard_view.xml',
        'wizard/academy_tests_change_owner_wizard_view.xml',
        'wizard/academy_tests_choose_report_wizard.xml',
        'wizard/academy_test_new_topic_version_wizard_view.xml',
        'wizard/academy_tests_questions_by_teacher_wizard_view.xml',
        'wizard/academy_tests_manual_categorization_wizard_view.xml',
        'wizard/academy_tests_remove_duplicate_questions_wizard_view.xml',
        'wizard/academy_tests_question_request_set_wizard_view.xml',
        'wizard/academy_tests_question_append_wizard_link_view.xml',
        'wizard/academy_tests_random_template_type_wizard_view.xml',
        'wizard/academy_tests_copy_assignments_wizard_view.xml',
        'wizard/academy_tests_assignment_wizard_view.xml',
        'wizard/academy_tests_attempt_wizard_view.xml',
        'wizard/academy_tests_test_question_block_position_view.xml',
        'wizard/academy_tests_test_question_shuffle_wizard_view.xml',
        'wizard/academy_tests_set_test_block_wizard_view.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/ir_attachment_demo.xml',
        'demo/academy_tests_tag_demo.xml',
        'demo/academy_tests_topic_demo.xml',
        'demo/academy_tests_topic_version_demo.xml',
        'demo/academy_tests_category_demo.xml',
        'demo/academy_tests_test_demo.xml',
        'demo/academy_tests_question_demo.xml',
        'demo/academy_tests_answer_demo.xml',
        'demo/academy_tests_test_question_rel_demo.xml',
        'demo/academy_training_module_demo.xml',
        'demo/academy_tests_random_template_demo.xml',
        'demo/academy_tests_random_line_demo.xml',
        'demo/academy_tests_random_line_categorization_demo.xml',
        'demo/academy_tests_attempt_demo.xml',
        'demo/academy_tests_attempt_answer_demo.xml',
        'demo/academy_tests_topic_training_module_link_demo.xml'
    ],
    'js': [
        'static/src/js/academy_tests.js',
        'static/src/js/listview_button.js'
    ],
    'css': [
        'static/src/css/styles-backend.css',
        'static/src/css/academy_tests_report.css',
    ],
    'qweb': [
        "static/src/xml/listview_button.xml"
    ],
    "external_dependencies": {
        "python": ['unidecode', 'dicttoxml', 'chardet', 'python-docx']
    },

    'license': 'AGPL-3'
}
