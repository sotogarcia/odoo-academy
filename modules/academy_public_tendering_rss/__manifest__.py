# -*- coding: utf-8 -*-
{
    'name': "academy_public_tendering_rss",

    'summary': """
    Allow following public tender offers through RSS feeds
    """,

    'description': """
        Allow following public tender offers through RSS feeds
    """,

    'author': 'Jorge Soto Garcia',
    'website': 'https://github.com/sotogarcia',

    'category': 'Academy',
    'version': '13.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['academy_public_tendering'],

    # always loaded
    'data': [
        'data/academy_public_tendering_rss_feed_data.xml',
        'data/ir_cron_data.xml',

        'security/academy_public_tendering_rss_feed.xml',
        'security/academy_public_tendering_rss_item.xml',

        'views/academy_public_tendering_rss.xml',
        'views/academy_public_tendering_rss_feed_view.xml',
        'views/academy_public_tendering_rss_item_view.xml',
        'views/academy_public_tendering_event_view.xml',
        'views/academy_public_tendering_offer_view.xml',
        'views/academy_public_tendering_event_process.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    "external_dependencies": {
        "python": ['feedparser']
    },
}


# - [x] Colocar en el menú
# - [x] Homogeneizar los nombres
# - [x] Homogeneizar la mensajería
# - [x] Comenzar con un máximo de 10 días de antelación (parametrizar)
# - [ ] Revisar la herencia
#       - Definir una función para leer el sumario
#       - Definir una función que llame al lector específico
# - [ ] Añadir la creación specializada de procesos selectivos
# - [ ] Añadir Lugo, Ourense, A Coruña
# Campo: Es un boletín oficial
# - Si es boletin oficial el enlace va a boletín oficial
# - Si no es boletín oficial, el enlace va a tablon de anuncios
#
# Relacionar con las ofertas formativas
# Relacionar con los procesos selectivos
# Creo que safe-date no se calcula bien
# Kanban y foto en las RSS
# Pivot en los items RSS