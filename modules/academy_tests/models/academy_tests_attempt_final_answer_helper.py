# -*- coding: utf-8 -*-
""" AcademyTestsAttemptAnswerRel

This module contains the academy.tests.attempt.answer.rel Odoo model which
stores the final academy answer for each question in academy tests attempt.
"""

from odoo import models, fields

from odoo.tools import drop_view_if_exists
from .utils.view_academy_tests_attempt_final_answer_helper import \
    ACADEMY_TESTS_ATTEMPT_FINAL_ANSWER_HELPER
from .utils.subquery_academy_tests_attempt_sanitized_answer import \
    SUBQUERY_ACADEMY_TESTS_ATTEMPT_SANITIZED_ANSWER
from odoo.tools.translate import _

from logging import getLogger

_logger = getLogger(__name__)


class AcademyTestsAttemptFinalAnswerHelper(models.Model):
    """ Builds a view with the final answer of each question in an attempt.
    This view will be used as middle table in many2many field to show final
    attempt answers by attempt.

    Only the following fields: attempt_id and attempt_answer_id, are
    required, all other can be usefull in a future.
    """

    _name = 'academy.tests.attempt.final.answer.helper'
    _description = u'Academy tests attempt final answer helper'

    _inherit = ['academy.abstract.attempt.answer']

    _rec_name = 'attempt_id'
    _order = 'attempt_id ASC, sequence ASC'

    _auto = False

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

    html = fields.Html(
        string='Html',
        related="question_id.html"
    )

    answer_id = fields.Many2one(
        string='Answer',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.answer',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    sequence = fields.Integer(
        string='Sequence',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Question sequence order'
    )

    is_correct = fields.Boolean(
        string='Is correct?',
        required=False,
        readonly=True,
        index=False,
        default=False,
        help='Checked means this is a right answer for the question',
        track_visibility='onchange'
    )

    retries = fields.Integer(
        string='Retry count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of times the user has changed the answer'
    )

    answer_count = fields.Integer(
        string='Answer count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of times the user marked the question as sure answer'
    )

    doubt_count = fields.Integer(
        string='Doubt count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of times the user marked the question as doubt'
    )

    blank_count = fields.Integer(
        string='Blank count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of times the user left the question blank'
    )

    right_count = fields.Integer(
        string='Right count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of times the user marked the answer correctly'
    )

    wrong_count = fields.Integer(
        string='Wrong count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of times the user marked the answer incorrectly'
    )

    aptly = fields.Float(
        string='Hit rate',
        required=False,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Percentage of times the user marked the right answer'
    )

    wrongly = fields.Float(
        string='Error rate',
        required=False,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Percentage of times the user marked the wrong answer'
    )

    @staticmethod
    def build_view_sql():
        outer = ACADEMY_TESTS_ATTEMPT_FINAL_ANSWER_HELPER
        inner = SUBQUERY_ACADEMY_TESTS_ATTEMPT_SANITIZED_ANSWER
        return outer.format(inner)

    def init(self):
        sentence = 'CREATE or REPLACE VIEW {} as ( {} )'

        drop_view_if_exists(self.env.cr, self._table)

        query = self.build_view_sql()
        self.env.cr.execute(sentence.format(self._table, query))

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

    def show_question(self):
        self.ensure_one()

        question_id = self.question_link_id.question_id.id

        return {
            'type': 'ir.actions.act_window',
            'name': _('Question #{}').format(question_id),
            'view_mode': 'form',
            'res_model': 'academy.tests.question',
            'target': 'new',
            'domain': [],
            'context': {},
            'res_id': question_id,
            'flags': {'initial_mode': 'view'}
        }

    def show_attempt_answers(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Attempt answers'),
            'view_mode': 'tree,form',
            'res_model': 'academy.tests.attempt.answer',
            'target': 'current',
            'domain': [
                ('attempt_id', '=', self.attempt_id.id),
                ('question_link_id', '=', self.question_link_id.id)
            ],
            'context': {}
        }
