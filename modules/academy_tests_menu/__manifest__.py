# -*- coding: utf-8 -*-
{
    'name': 'Academy Tests Menu',

    'summary': '''
        Menu to easy admin academy tests information''',

    'description': '''
        Menu to easy admin academy tests information
    ''',

    'author': 'Jorge Soto Garcia',
    'website': 'https://github.com/sotogarcia',

    'category': 'Academy',
    'version': '13.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': [
        'mail',
        'web',
        'academy_base',
        'academy_tests',
        'academy_laravel_frontend'
    ],
    'data': [
        'views/academy_tests_main_menu.xml'
    ],
    'demo': [

    ],
    'js': [

    ],
    'css': [

    ],
    'qweb': [
    ],
    "external_dependencies": {
    },

    'license': 'AGPL-3'
}
