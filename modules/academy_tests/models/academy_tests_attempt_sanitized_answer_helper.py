# -*- coding: utf-8 -*-
""" AcademyTestsAttemptAnswer

This module contains the academy.tests.attempt.answer Odoo model which stores
all academy tests attempt answer attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger

from odoo.tools import drop_view_if_exists
from .utils.view_academy_tests_attempt_sanitized_answer_helper import \
    ACADEMY_TESTS_ATTEMPT_SANITIZED_ANSWER_HELPER

_logger = getLogger(__name__)


class AcademyTestAttemptSanitizedAnswerHelper(models.Model):
    """ Logs all student answers in a test attempt, even if later he
    change it by another answer
    """

    _name = 'academy.tests.attempt.sanitized.answer.helper'
    _description = u'Academy tests attempt sanitized answer helper'

    _inherit = ['academy.abstract.attempt.answer']

    _rec_name = 'id'
    _order = 'instant DESC'

    _auto = False

    _view_sql = ACADEMY_TESTS_ATTEMPT_SANITIZED_ANSWER_HELPER

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
