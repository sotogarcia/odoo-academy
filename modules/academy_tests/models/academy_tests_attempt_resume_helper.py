# -*- coding: utf-8 -*-
""" AcademyTestsAttemptResumeHelper

This module contains the academy.competency.unit Odoo model which stores
all competency unit attributes and behavior.
"""

from odoo import models, fields, api
from logging import getLogger

from odoo.tools import drop_view_if_exists
from .utils.view_academy_tests_attempt_resume_helper import \
    ACADEMY_TESTS_ATTEMPT_RESUME_HELPER
from .utils.subquery_academy_tests_attempt_sanitized_answer import \
    SUBQUERY_ACADEMY_TESTS_ATTEMPT_SANITIZED_ANSWER
from odoo.tools.translate import _

from re import split as regex_split, IGNORECASE
from odoo.exceptions import UserError

_logger = getLogger(__name__)


class AcademyTestsAttemptResumeHelper(models.Model):
    """ Odoo model based in a SQL view. This will be used by Laravel.
    """

    _name = 'academy.tests.attempt.resume.helper'
    _description = u'Academy tests attempt resume helper'

    _rec_name = 'id'
    _order = 'id DESC'

    _inherit = ['academy.abstract.attempt']

    _auto = False

    test_id = fields.Many2one(
        string='Test',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Test will be assigned to the chosen training item',
        comodel_name='academy.tests.test',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    attempt_id = fields.Many2one(
        string='Attempt',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Test attempt for which these statistics were generated',
        comodel_name='academy.tests.attempt',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    description = fields.Text(
        string='Description',
        readonly=True,
        help='Something about this attempt',
        related='attempt_id.description'
    )

    question_count = fields.Integer(
        string='Question count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of questions in test',
        group_operator="avg"
    )

    answered_count = fields.Integer(
        string='Answered count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of final answered questions',
        group_operator="avg"
    )

    right_count = fields.Integer(
        string='Right count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of final right answers',
        group_operator="avg"
    )

    wrong_count = fields.Integer(
        string='Wrong count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of final wrong answers',
        group_operator="avg"
    )

    blank_count = fields.Integer(
        string='Blank count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of final blank answers',
        group_operator="avg"
    )

    answer_count = fields.Integer(
        string='Answer count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of final answers marked as answered',
        group_operator="avg"
    )

    doubt_count = fields.Integer(
        string='Doubt count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of final answers marked as doubt',
        group_operator="avg"
    )

    right_points = fields.Float(
        string='Right points',
        required=False,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Final score obtained based on right answers',
        group_operator="avg"
    )

    wrong_points = fields.Float(
        string='Wrong points',
        required=False,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Final score obtained based on wrong answers',
        group_operator="avg"
    )

    blank_points = fields.Float(
        string='Blank points',
        required=False,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Final score obtained based on blank answers',
        group_operator="avg"
    )

    final_points = fields.Float(
        string='Final points',
        required=False,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Final attempt score',
        group_operator="avg"
    )

    max_points = fields.Float(
        string='Maximum points',
        required=False,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Maximum number of points the student can obtain',
        group_operator="max"
    )

    right_percent = fields.Float(
        string='Right percent',
        required=False,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Percentage of questions answered correctly over the total',
        group_operator="avg"
    )

    wrong_percent = fields.Float(
        string='Wrong percent',
        required=False,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Percentage of questions answered incorrectly over the total',
        group_operator="avg"
    )

    blank_percent = fields.Float(
        string='Blank percent',
        required=False,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Percentage of questions answered blank over the total',
        group_operator="avg"
    )

    answered_percent = fields.Float(
        string='Answered percent',
        required=False,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Percentage of questions answered over the total',
        group_operator="avg"
    )

    passed = fields.Boolean(
        string='Passed',
        required=False,
        readonly=True,
        index=False,
        default=False,
        help='Checked if the obtained score reaches half of the maximum score'
    )

    grade = fields.Selection(
        string='Grade',
        required=False,
        readonly=True,
        index=False,
        default='fail',
        help='Passed if the obtained score reaches half of the maximum score',
        selection=[
            ('pass', 'Passing grade'),
            ('fail', 'Failing grade')
        ]
    )

    right_score = fields.Float(
        string='Right score',
        required=False,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Right answers score computed over 10 points',
        group_operator="avg"
    )

    wrong_score = fields.Float(
        string='Wrong score',
        required=False,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Wrong answers score computed over 10 points',
        group_operator="avg"
    )

    blank_score = fields.Float(
        string='Blank score',
        required=False,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Blank answers score computed over 10 points',
        group_operator="avg"
    )

    final_score = fields.Float(
        string='Final score',
        required=False,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Final attempt score computed over 10 points',
        group_operator="avg"
    )

    test_owner_id = fields.Many2one(
        string='Test owner',
        readonly=True,
        related="test_id.owner_id"
    )

    final_answer_helper_ids = fields.One2many(
        string='Final answer statistics',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='False',
        comodel_name='academy.tests.attempt.final.answer.helper',
        inverse_name='attempt_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    rating = fields.Integer(
        string='Rating',
        required=False,
        readonly=False,
        index=False,
        default=0,
        help=('Final attempt score computed over 10 points and truncated to '
              'the nearest lower integer')
    )

    rank = fields.Integer(
        string='Rank',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Rank of the attempts by assignment and user'
    )

    @staticmethod
    def _build_view_sql():
        outer = ACADEMY_TESTS_ATTEMPT_RESUME_HELPER
        inner = SUBQUERY_ACADEMY_TESTS_ATTEMPT_SANITIZED_ANSWER
        return outer.format(inner)

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
        view_sql = self._build_view_sql()
        pattern = '''CREATE or REPLACE VIEW {} as ({})'''
        sentence = pattern.format(self._table, view_sql)

        drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(sentence)

        self.prevent_actions()

    scale_pattern = fields.Char(
        string='Scale (pattern)',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Display correction scale values in a text string',
        size=15,
        translate=False,
        compute='_compute_scale_pattern',
        search='_search_scale_pattern'
    )

    @api.depends('right', 'wrong', 'blank')
    def _compute_scale_pattern(self):
        pattern = 'R{:+n}W{:+n}B{:+n}'

        for record in self:
            record.scale_pattern = pattern.format(
                record.right, record.wrong, record.blank)

    def _search_scale_pattern(self, operator, value):

        if operator in ['=']:
            msg = _('Only equal comparison is allowed')
            raise UserError(msg)

        splitted = regex_split('[RWB]', value, flags=IGNORECASE)

        try:
            values = [float(item) for item in splitted if item]
            assert len(values) == 3
        except (ValueError, TypeError, AssertionError):
            msg = _('Invalid correction scale pattern')
            raise UserError(msg)

        domain = [
            ('right', '=', values[0]),
            ('wrong', '=', values[1]),
            ('blank', '=', values[2])
        ]

        return domain

    def show_attempt(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': self.attempt_id.display_name,
            'view_mode': 'form',
            'res_model': 'academy.tests.attempt',
            'target': 'current',
            'domain': [],
            'context': {},
            'res_id': self.attempt_id.id
        }
