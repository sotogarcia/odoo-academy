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

    'license': 'LGPL-3',
    'category': 'Academy',
    'version': '15.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': [
        'mail',
        'web',
        'academy_base',
        'ks_percent_field'
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
        'security/academy_tests_category.xml',
        'security/academy_tests_level.xml',
        'security/academy_tests_question.xml',
        'security/academy_tests_question_impugnment.xml',
        'security/academy_tests_question_impugnment_reply.xml',
        'security/academy_tests_tag.xml',
        'security/academy_tests_test.xml',
        'security/academy_tests_test_question_rel.xml',
        'security/academy_tests_question_type.xml',
        'security/academy_tests_topic.xml',

        'security/academy_tests_topic_training_module_link.xml',
        'security/academy_tests_test_kind.xml',
        'security/academy_tests_attempt.xml',
        'security/academy_tests_attempt_answer.xml',
        'security/academy_tests_correction_scale.xml',

        'security/academy_tests_topic_version.xml',

        'security/mail_message.xml',
        'security/academy_tests_uncategorized_questions_by_user.xml',
        'security/academy_tests_test_block.xml',
        'security/academy_tests_attempt_resume_helper.xml',
        'security/academy_tests_test_training_module_helper.xml',
        'security/academy_tests_attempt_final_answer_helper.xml',
        'security/ir_attachment.xml',
        'security/academy_tests_test_training_assignment.xml',

        'security/academy_tests_question_import_wizard.xml',
        'security/academy_tests_change_owner_wizard.xml',
        'security/academy_tests_choose_report_wizard.xml',
        'security/academy_tests_manual_categorization_wizard.xml',
        'security/academy_tests_questions_by_teacher_wizard.xml',
        'security/academy_tests_question_append_wizard.xml',
        'security/academy_tests_question_append_wizard_link.xml',
        'security/academy_tests_question_categorize_wizard.xml',

        'security/academy_tests_remove_duplicate_questions_wizard.xml',
        'security/academy_tests_update_questions_wizard.xml',
        'security/academy_tests_new_topic_version_wizard.xml',

        # This must be before academy_tests_tets_view.xml
        'report/academy_test_report.xml',

        'views/academy_tests.xml',
        'views/academy_tests_answer_view.xml',
        'views/academy_tests_category_view.xml',
        'views/academy_tests_level_view.xml',
        'views/academy_tests_question_impugnment_view.xml',
        'views/academy_tests_question_impugnment_reply_view.xml',
        'views/academy_tests_question_view.xml',
        'views/academy_tests_tag_view.xml',
        'views/academy_tests_test_question_rel_view.xml',
        'views/academy_tests_test_kind_view.xml',
        'views/academy_tests_tets_view.xml',
        'views/academy_tests_topic_view.xml',
        'views/ir_attachment_view.xml',

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


        'views/academy_tests_uncategorized_by_user_readonly_view.xml',
        'views/academy_tests_test_block_view.xml',
        'views/academy_tests_attempt_resume_helper_view.xml',
        'views/academy_tests_attempt_final_answer_helper_view.xml',

        'views/academy_tests_test_training_assignment_view.xml',

        'report/academy_test_answers_table_report.xml',
        'report/academy_training_activity_details_with_topics_report.xml',
        'report/academy_statistics_student_question_readonly_report.xml',
        'report/academy_tests_uncategorized_by_user_report.xml',

        'report/academy_tests_test_text_report.xml',

        'templates/uncategorized_questions_by_user_and_topic.xml',
        'templates/duplicated_questions_by_user_and_topic.xml',
        'templates/mail_template_you_have_impugnments.xml',
        'templates/check_training_module.xml',
        'templates/check_competency_unit.xml',

        'wizard/academy_tests_question_categorize_wizard_view.xml',
        'wizard/academy_tests_question_append_wizard_view.xml',
        'wizard/academy_tests_question_import_wizard_view.xml',
        'wizard/academy_tests_update_questions_wizard_view.xml',

        'wizard/academy_tests_change_owner_wizard_view.xml',
        'wizard/academy_tests_choose_report_wizard.xml',
        'wizard/academy_tests_new_topic_version_wizard_view.xml',
        'wizard/academy_tests_questions_by_teacher_wizard_view.xml',
        'wizard/academy_tests_manual_categorization_wizard_view.xml',
        'wizard/academy_tests_remove_duplicate_questions_wizard_view.xml',
        'wizard/academy_tests_question_append_wizard_link_view.xml',
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

        'demo/academy_tests_attempt_demo.xml',
        'demo/academy_tests_attempt_answer_demo.xml',
        'demo/academy_tests_topic_training_module_link_demo.xml'
    ],
    'js': [

    ],
    'css': [
        'static/src/css/styles-backend.css',
        'static/src/css/academy_tests_report.css',
    ],
    'qweb': [
    ],
    "external_dependencies": {
        "python": ['unidecode', 'dicttoxml', 'chardet', 'python-docx']
    },

    # always loaded
    "assets": {
        'web.assets_backend': [
            "academy_tests/static/src/css/styles-backend.css",
            "academy_tests/static/src/js/academy_tests.js"
        ],
        'web.report_assets_common': [
            'academy_tests/static/src/css/academy_tests_report.css',
            'academy_tests/static/src/css/academy_training_activity_details_with_topics_relationships_report.css'
        ]
    },

    'license': 'AGPL-3'
}
