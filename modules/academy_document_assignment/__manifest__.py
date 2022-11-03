# -*- coding: utf-8 -*-
{
    'name': "Academy Document Assignments",

    'summary': 'Allows you to assign documents from DMS to training elements',

    'author': "Jorge Soto Garcia",
    'website': "https://github.com/sotogarcia",

    'license': 'LGPL-3',
    'category': 'Technical Settings',
    'version': '15.0.1.3',

    'depends': [
        'base',
        'mail',
        'record_ownership',
        'academy_base',
        'dms'
    ],

    'data': [
        'security/academy_document_assignment.xml',
        'views/academy_document_assignment_view.xml',
    ],

    'demo': [
        'demo/academy_document_assignment_demo.xml',
    ],

    'auto_install': True
}
