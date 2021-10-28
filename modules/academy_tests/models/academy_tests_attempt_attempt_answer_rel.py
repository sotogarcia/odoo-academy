# -*- coding: utf-8 -*-
""" AcademyTestsAttemptAnswerRel

This module contains the academy.tests.attempt.answer.rel Odoo model which
stores the final academy answer for each question in academy tests attempt.
"""

from odoo import models, fields

from odoo.tools import drop_view_if_exists
from .utils.view_academy_tests_attempt_attempt_answer_rel import \
    ACADEMY_TESTS_ATTEMPT_ATTEMPT_ANSWER_REL_MODEL

from logging import getLogger

_logger = getLogger(__name__)


class AcademyTestsAttemptAttemptAnswerRel(models.Model):
    """ Builds a view with the final answer of each question in an attempt.
    This view will be used as middle table in many2many field to show final
    attempt answers by attempt.

    A Many2manyThroughView custom field can not be used because this model
    has serveral extra fields.

    Only the following fields: attempt_id and attempt_answer_id, are
    required, all other can be usefull in a future.
    """

    _name = 'academy.tests.attempt.attempt.answer.rel'
    _description = u'Academy tests attempt attempt answer rel'

    _rec_name = 'attempt_id'
    _order = 'attempt_id ASC, sequence ASC'

    _auto = False

    _view_sql = ACADEMY_TESTS_ATTEMPT_ATTEMPT_ANSWER_REL_MODEL

    attempt_id = fields.Many2one(
        string='Attempt',
        required=True,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.attempt',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    attempt_answer_id = fields.Many2one(
        string='Attempt answer',
        required=True,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.attempt.answer',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    question_link_id = fields.Many2one(
        string='Test-question link',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.test.question.rel',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    test_id = fields.Many2one(
        string='Test',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.test',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    question_id = fields.Many2one(
        string='Question',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.question',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    instant = fields.Datetime(
        string='Instant',
        required=True,
        readonly=False,
        index=False,
        default=fields.datetime.now(),
        help=False
    )

    sequence = fields.Integer(
        string='Sequence',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help=False
    )

    def init(self):
        sentence = 'CREATE or REPLACE VIEW {} as ( {} )'

        drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute(sentence.format(self._table, self._view_sql))

        self.prevent_actions()

    def prevent_actions(self):
        actions = ['INSERT', 'UPDATE', 'DELETE']

        BASE_SQL = '''
            CREATE OR REPLACE RULE {table}_{action} AS
                ON {action} TO {table} DO INSTEAD NOTHING
        '''

        for action in actions:
            sql = BASE_SQL.format(table=self._table, action=action)
            self.env.cr.execute(sql)
