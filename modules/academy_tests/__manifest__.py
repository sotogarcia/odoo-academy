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
    'version': '15.0.1.3',

    # any module necessary for this one to work correctly
    'depends': [
        'mail',
        'web',
        'record_ownership',
        'base_field_m2m_view',
        'ks_percent_field'
    ],

    # always loaded
    'data': [
        'data/mail_message_subtype_data.xml',
        'data/academy_tests_level_data.xml',
        'data/academy_tests_question_type_data.xml',
        'data/academy_tests_test_kind_data.xml',
        'data/ir_sequence.xml',
        'data/academy_tests_block_data.xml',

        'data/academy_tests_topic_data.xml',
        'data/academy_tests_version_data.xml',
        'data/academy_tests_category_data.xml',

        'data/res_groups_data.xml',

        'security/academy_tests.xml',
        'security/academy_tests_abstract_test_details.xml',
        'security/academy_tests_answer.xml',
        'security/academy_tests_answers_table.xml',
        'security/academy_tests_category.xml',
        'security/academy_tests_level.xml',
        'security/academy_tests_question.xml',
        'security/academy_tests_tag.xml',
        'security/academy_tests_test.xml',
        'security/academy_tests_test_question_rel.xml',
        'security/academy_tests_question_type.xml',
        'security/academy_tests_topic.xml',
        'security/academy_tests_test_kind.xml',
        'security/academy_tests_version.xml',
        'security/academy_tests_block.xml',
        'security/mail_message.xml',
        'security/ir_attachment.xml',

        'security/academy_tests_question_import_wizard.xml',
        'security/academy_tests_change_owner_wizard.xml',
        'security/academy_tests_choose_report_wizard.xml',
        'security/academy_tests_manual_categorization_wizard.xml',
        'security/academy_tests_question_append_wizard.xml',
        'security/academy_tests_question_append_wizard_link.xml',
        'security/academy_tests_question_categorize_wizard.xml',
        'security/academy_tests_update_questions_wizard.xml',
        'security/academy_tests_new_version_wizard.xml',

        'security/academy_tests_question_dependency_rel.xml',
        'security/academy_tests_block_rel.xml',
        'security/academy_tests_topic_rel.xml',

        # This must be before academy_tests_tets_view.xml
        'report/academy_test_report.xml',

        'views/academy_tests.xml',

        'views/academy_tests_answer_view.xml',
        'views/academy_tests_category_view.xml',
        'views/academy_tests_level_view.xml',
        'views/academy_tests_question_view.xml',
        'views/academy_tests_tag_view.xml',
        'views/academy_tests_test_question_rel_view.xml',
        'views/academy_tests_test_kind_view.xml',
        'views/academy_tests_tets_view.xml',
        'views/academy_tests_topic_view.xml',
        'views/academy_tests_version_view.xml',
        'views/academy_tests_block_view.xml',

        'views/ir_attachment_view.xml',
        'views/res_config_settings.xml',

        'report/academy_test_answers_table_report.xml',
        'report/academy_tests_test_text_report.xml',

        'wizard/academy_tests_question_categorize_wizard_view.xml',
        'wizard/academy_tests_question_append_wizard_view.xml',
        'wizard/academy_tests_question_import_wizard_view.xml',
        'wizard/academy_tests_update_questions_wizard_view.xml',
        'wizard/academy_tests_change_owner_wizard_view.xml',
        'wizard/academy_tests_choose_report_wizard.xml',
        'wizard/academy_tests_new_version_wizard_view.xml',
        'wizard/academy_tests_manual_categorization_wizard_view.xml',
        'wizard/academy_tests_question_append_wizard_link_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/ir_attachment_demo.xml',
        'demo/academy_tests_tag_demo.xml',
        'demo/academy_tests_topic_demo.xml',
        'demo/academy_tests_version_demo.xml',
        'demo/academy_tests_category_demo.xml',
        'demo/academy_tests_test_demo.xml',
        'demo/academy_tests_question_demo.xml',
        'demo/academy_tests_answer_demo.xml',
        'demo/academy_tests_test_question_rel_demo.xml'
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

    # always loaded
    "assets": {
        'web.assets_backend': [
            "academy_tests/static/src/css/styles-backend.css",
            "academy_tests/static/src/js/academy_tests.js",
            "academy_tests/static/src/js/listview_button.js",
        ],
        'web.report_assets_common': [
            'academy_tests/static/src/css/academy_tests_report.css',
        ]
    },
}
