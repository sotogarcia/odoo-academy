# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from . import models
from . import controllers
from . import wizard

from .utils.sql_helpers import execute_sql_script, install_extension


def pre_init_hook(cr):
    """
    This method is executed before the module installation begins.

    :param cr: database cursor
    """

    rel_path = ('academy_base', 'data')
    execute_sql_script(cr, rel_path, 'pre_init_hook.sql', 'pre_init_hook')


def post_init_hook(cr, registry):
    """
    This method is executed after the module installation is completed.

    :param cr: database cursor
    :param registry: Odoo registry object
    """

    install_extension(cr, 'btree_gist')

    rel_path = ('academy_base', 'data')
    execute_sql_script(cr, rel_path, 'post_init_hook.sql', 'post_init_hook')


def uninstall_hook(cr, registry):
    """
    This method is executed before the module uninstallation begins.

    :param cr: database cursor
    :param registry: Odoo registry object
    """

    rel_path = ('academy_base', 'data')
    execute_sql_script(cr, rel_path, 'uninstall_hook.sql', 'uninstall_hook')
