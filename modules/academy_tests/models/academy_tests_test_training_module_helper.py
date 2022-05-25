# -*- coding: utf-8 -*-
""" AcademyTestsTestTrainingModuleHelper

IMPORTANT: This model was in academy_laravel_frontent module. I have move it
to this module to prevent SQL dependency errors.
"""

from odoo import models
from logging import getLogger

from odoo.tools import drop_view_if_exists
from .utils.view_academy_tests_test_training_module_helper import \
    ACADEMY_TESTS_TEST_TRAINING_MODULE_HELPER


_logger = getLogger(__name__)


class AcademyTestsTestTrainingModuleHelper(models.Model):
    """ Odoo model based in a SQL view. This will be used by Laravel.
    """

    _name = 'academy.tests.test.training.module.helper'
    _description = u'Academy tests test training module helper'

    _rec_name = 'id'
    _order = 'id DESC'

    _auto = False

    _view_sql = ACADEMY_TESTS_TEST_TRAINING_MODULE_HELPER

    def prevent_actions(self):
        actions = ['INSERT', 'UPDATE', 'DELETE']

        BASE_SQL = '''
            CREATE OR REPLACE RULE {table}_{action} AS
                ON {action} TO {table} DO INSTEAD NOTHING
        '''

        for action in actions:
            sql = BASE_SQL.format(table=self._table, action=action)
            self.env.cr.execute(sql)

    def init(self):
        pattern = '''CREATE or REPLACE VIEW {} as ({})'''
        sentence = pattern.format(self._table, self._view_sql)

        drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute(sentence)

        self.prevent_actions()
