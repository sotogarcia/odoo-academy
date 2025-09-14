# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from . import models
from . import controllers
from . import wizard

from .utils.sql_helpers import execute_sql_script, install_extension


def pre_init_hook(env):
    """Executed before the module installation begins."""
    rel_path = ("academy_base", "data")
    execute_sql_script(env, rel_path, "pre_init_hook.sql", "pre_init_hook")


def post_init_hook(env):
    """Executed after the module installation is completed."""
    install_extension(env, "btree_gist")
    rel_path = ("academy_base", "data")
    execute_sql_script(env, rel_path, "post_init_hook.sql", "post_init_hook")


def uninstall_hook(env):
    """Executed before the module uninstallation begins."""
    rel_path = ("academy_base", "data")
    execute_sql_script(env, rel_path, "uninstall_hook.sql", "uninstall_hook")

