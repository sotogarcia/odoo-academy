# -*- coding: utf-8 -*-
""" AcademyTestsAttemptResumeHelper

This module contains the academy.competency.unit Odoo model which stores
all competency unit attributes and behavior.
"""

from odoo import models, fields
from logging import getLogger

from odoo.tools import drop_view_if_exists
from .utils.view_academy_tests_attempt_resume_helper import \
    ACADEMY_TESTS_ATTEMPT_RESUME_HELPER
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


_logger = getLogger(__name__)


class AcademyTestsAttemptResumeHelper(models.Model):
    """ Odoo model based in a SQL view. This will be used by Laravel.
    """

    _name = 'academy.tests.attempt.resume.helper'
    _description = u'Academy tests attempt resume helper'

    _rec_name = 'id'
    _order = 'id DESC'

    _auto = False

    _view_sql = ACADEMY_TESTS_ATTEMPT_RESUME_HELPER

    questions = fields.Integer(
        string='Questions',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of questions in test'
    )

    answered = fields.Integer(
        string='Answered',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of final answered questions'
    )

    right = fields.Integer(
        string='Right',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of final right answers'
    )

    wrong = fields.Integer(
        string='Wrong',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of final wrong answers'
    )

    answer = fields.Integer(
        string='Answer',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of final answers marked as answered'
    )

    doubt = fields.Integer(
        string='Doubt',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of final answers marked as doubt'
    )

    right_points = fields.Float(
        string='Right points',
        required=False,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Final score obtained based on right answers'
    )

    wrong_points = fields.Float(
        string='Wrong points',
        required=False,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Final score obtained based on wrong answers'
    )

    blank_points = fields.Float(
        string='Blank points',
        required=False,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Final score obtained based on blank answers'
    )

    final_points = fields.Float(
        string='Final points',
        required=False,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Final attempt score'
    )

    max_points = fields.Float(
        string='Maximum points',
        required=False,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Maximum number of points the student can obtain'
    )

    def prevent_actions(self):
        actions = ['INSERT', 'UPDATE', 'DELETE']

        BASE_SQL = '''
            CREATE OR REPLACE RULE {table}_{action} AS
                ON {action} TO {table} DO INSTEAD NOTHING
        '''

        for action in actions:
            sql = BASE_SQL.format(table=self._table, action=action)
            self.env.cr.execute(sql)

    def _is_tablefunc_installed(self):
        sentence = 'select oid from pg_extension where extname=\'tablefunc\''

        self.env.cr.execute(sentence)
        result = len(self.env.cr.fetchall()) == 1

        if result:
            _logger.debug('PostgreSQL tablefunc extension has been found')
        else:
            _logger.debug('PostgreSQL tablefunc extension has not been found')

        return result

    def init(self):
        pattern = '''CREATE or REPLACE VIEW {} as ({})'''
        sentence = pattern.format(self._table, self._view_sql)

        if not self._is_tablefunc_installed():
            msg = _('Postgres extension "tablefunc" is required. '
                    'You must manually execute following SQL query: '
                    'CREATE EXTENSION IF NOT EXISTS tablefunc;')
            raise ValidationError(msg)

        drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(sentence)

        self.prevent_actions()
