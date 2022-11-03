# -*- coding: utf-8 -*-
{
    'name': "Civil Service Recruitment",

    'summary': """
        Store and manage information about civil service entrance examination""",

    'description': """
        Store and manage information about civil service entrance examination
    """,

    'author': "Jorge Soto Garcia",
    'website': "https://github.com/sotogarcia",

    'license': 'LGPL-3',
    'category': 'Academy',
    'version': '15.0.1.3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'mail',
        'record_ownership',
        'base_field_m2m_view'
    ],

    # always loaded
    'data': [
        'data/res_groups_data.xml',
        'data/res_partner_category_data.xml',
        'data/res_partner_data.xml',
        'data/civil_service_recruitment_employment_group_data.xml',
        'data/civil_service_recruitment_public_corps_data.xml',
        'data/civil_service_recruitment_access_system_data.xml',
        'data/civil_service_recruitment_exam_type_data.xml',
        'data/civil_service_recruitment_hiring_type_data.xml',
        'data/civil_service_recruitment_vacancy_position_type.xml',
        'data/civil_service_recruitment_public_administration_type_data.xml',
        'data/civil_service_recruitment_public_administration_data.xml',
        'data/civil_service_recruitment_event_type_data.xml',
        'data/ir_cron.xml',
        'data/mail_message_subtype_data.xml',

        'security/civil_service_recruitment_hiring_type.xml',
        'security/civil_service_recruitment_employment_group.xml',
        'security/civil_service_recruitment_exam_type.xml',
        'security/civil_service_recruitment_process.xml',
        'security/civil_service_recruitment_vacancy_position_type.xml',
        'security/civil_service_recruitment_public_corps.xml',
        'security/civil_service_recruitment_vacancy_position.xml',
        'security/civil_service_recruitment_access_system.xml',
        'security/civil_service_recruitment_public_administration.xml',
        'security/civil_service_recruitment_public_administration_type.xml',
        'security/civil_service_recruitment_public_offer.xml',
        'security/civil_service_recruitment_event.xml',
        'security/civil_service_recruitment_event_type.xml',
        'security/civil_service_recruitment_required_specialization.xml',

        'views/civil_service_recruitment.xml',

        'views/civil_service_recruitment_employment_group_view.xml',
        'views/civil_service_recruitment_exam_type_view.xml',
        'views/civil_service_recruitment_hiring_type_view.xml',
        'views/civil_service_recruitment_vacancy_position_type_view.xml',
        'views/civil_service_recruitment_public_corps_view.xml',
        'views/civil_service_recruitment_vacancy_position_view.xml',
        'views/civil_service_recruitment_process_view.xml',
        'views/civil_service_recruitment_access_system_view.xml',
        'views/civil_service_recruitment_public_administration_view.xml',
        'views/civil_service_recruitment_public_administration_type_view.xml',
        'views/civil_service_recruitment_public_offer_view.xml',
        'views/civil_service_recruitment_event_view.xml',
        'views/civil_service_recruitment_event_type_view.xml',
        'views/civil_service_recruitment_required_specialization_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/res_partner_demo.xml',
        'demo/civil_service_recruitment_public_administration_demo.xml',
        'demo/civil_service_recruitment_public_offer_demo.xml',
        'demo/civil_service_recruitment_public_process_demo.xml',
        'demo/civil_service_recruitment_vacancy_position_demo.xml',
        'demo/civil_service_recruitment_event_demo.xml',
    ],
    'js': [
    ],
    'css': [
    ],

    # always loaded
    "assets": {
        "web_assets_backend": [
            "civil_service_recruitment/static/src/css/styles-backend.css",
        ]
    },

}
