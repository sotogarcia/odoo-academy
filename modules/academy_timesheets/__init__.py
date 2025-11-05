# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from . import models
from . import report

from . import wizard
from . import controllers


from odoo.addons.academy_base.utils.sql_helpers import execute_sql_script


def pre_init_hook(env):
    """Run before module installation."""
    rel_path = ("academy_timesheets", "data")
    execute_sql_script(env, rel_path, "pre_init_hook.sql", "pre_init_hook")


def post_init_hook(env):
    """Run right after module installation."""
    rel_path = ("academy_timesheets", "data")
    execute_sql_script(env, rel_path, "post_init_hook.sql", "post_init_hook")


def uninstall_hook(env):
    """Run after module uninstallation to cleanup."""
    rel_path = ("academy_timesheets", "data")
    execute_sql_script(env, rel_path, "uninstall_hook.sql", "uninstall_hook")
