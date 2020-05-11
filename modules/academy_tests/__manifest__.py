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
    ],

    # always loaded
    'data': [
        'data/academy_tests_level_data.xml',
        'data/academy_tests_question_type_data.xml',
        'data/ir_actions_server_data.xml',
        'data/academy_tests_test_kind_data.xml',

        'security/academy_tests.xml',
        'security/academy_tests_answer.xml',
        'security/academy_tests_answers_table.xml',
        'security/academy_tests_category.xml',
        'security/academy_tests_level.xml',
        'security/academy_tests_question.xml',
        'security/academy_tests_question_impugnment.xml',
        'security/academy_tests_tag.xml',
        'security/academy_tests_test.xml',
        'security/academy_tests_test_question_rel.xml',
        'security/academy_tests_question_type.xml',
        'security/academy_tests_topic.xml',
        'security/academy_tests_random_line.xml',
        'security/academy_tests_random_template.xml',
        'security/academy_tests_topic_training_module_link.xml',
        'security/academy_tests_test_kind.xml',

        'views/academy_tests.xml',
        'views/academy_tests_answer_view.xml',
        'views/academy_tests_category_view.xml',
        'views/academy_tests_level_view.xml',
        'views/academy_tests_question_impugnment_view.xml',
        'views/academy_tests_question_view.xml',
        'views/academy_tests_tag_view.xml',
        'views/academy_tests_test_question_rel_view.xml',
        'views/academy_tests_test_kind_view.xml',
        'views/academy_tests_tets_view.xml',
        'views/academy_tests_topic_view.xml',
        'views/ir_attachment_view.xml',
        'views/academy_tests_random_line_view.xml',
        'views/academy_tests_random_template_view.xml',

        'views/academy_tests_topic_training_module_link_view.xml',
        'views/academy_training_module_view.xml',

        'report/academy_tests_report_assets.xml',
        'report/academy_test_report.xml',
        'report/academy_test_answers_table_report.xml',

        'wizard/academy_tests_question_categorize_wizard_view.xml',
        'wizard/academy_tests_question_append_wizard_view.xml',
        'wizard/academy_tests_question_import_wizard_view.xml',

        'wizard/academy_tests_random_wizard_view.xml',
        'wizard/academy_tests_change_owner_wizard_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/academy_tests_tag_demo.xml',
        'demo/academy_tests_topic_demo.xml',
        'demo/academy_tests_category_demo.xml',
        'demo/academy_tests_test_demo.xml',
        'demo/academy_tests_question_demo.xml',
        'demo/academy_tests_answer_demo.xml',
        'demo/academy_tests_test_question_rel_demo.xml',
    ],
    'js': [
        'static/src/js/academy_tests.js'
    ],
    'css': [
        'static/src/css/styles-backend.css',
        'static/src/css/academy_tests_report.css'
    ],

    'license': 'AGPL-3'
}

