# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from odoo.tools import drop_view_if_exists
from .utils.view_academy_statistics_student_question_readonly import \
    ACADEMY_STATISTICS_STUDENT_QUESTION_READONLY_MODEL

from logging import getLogger


_logger = getLogger(__name__)


class AcademyStatisticsStudentQuestionReadonly(models.Model):
    """ Uses an SQL view to generate generate statistics relative to the
    answers given by students to each question
    """

    _name = 'academy.statistics.student.question.readonly'
    _description = u'Academy statistics student question readonly'

    _rec_name = 'id'
    _order = 'student_id, question_id ASC'

    _table = 'academy_statistics_student_question_readonly'
    _auto = False

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=False,
        size=1024,
        translate=True,
        related='question_id.name'
    )

    student_id = fields.Many2one(
        string='Student',
        required=True,
        readonly=True,
        index=False,
        default=None,
        help='Student related with the statistics record',
        comodel_name='academy.student',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    question_id = fields.Many2one(
        string='Question',
        required=True,
        readonly=True,
        index=False,
        default=None,
        help='Question related with the statistics record',
        comodel_name='academy.tests.question',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    attempts = fields.Integer(
        string='Attempts',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help='Number of attempts for question'
    )

    answer = fields.Integer(
        string='Answer',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help='Number of times the student answered the question with no doubt'
    )

    answer_percent = fields.Float(
        string='Answer percent',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Percentage of answers with no doubt'
    )

    doubt = fields.Integer(
        string='Doubt',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help='Number of times the student answered the question with doubt'
    )

    doubt_percent = fields.Float(
        string='Doubt percent',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Percentage of answers with doubt'
    )

    blank = fields.Integer(
        string='Blank',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help='Number of times the student did not answer the question'
    )

    blank_percent = fields.Float(
        string='Blank percent',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Percentage of times the student did not answer the question'
    )

    right = fields.Integer(
        string='Right',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help='Number of times the student answered the question correctly'
    )

    right_percent = fields.Float(
        string='Right percent',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Percentage of times the student answered the question correctly'
    )

    wrong = fields.Integer(
        string='Wrong',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help=('Number of times the student did not answer the question '
              'correctly')
    )

    wrong_percent = fields.Float(
        string='Wrong percent',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help=('Percentage of times the student did not answer the question '
              'correctly')
    )

    answer_doubt = fields.Integer(
        string='Answer/doubt',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help=('Number of times the student answered the question with or '
              'without doubt')
    )

    answer_doubt_percent = fields.Float(
        string='Answer/doubt percent',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help=('Percentage of times the student answered the question with or '
              'without doubt')
    )

    blank_doubt = fields.Integer(
        string='Blank/doubt',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help=('Number of times the student did not answer the question or '
              'answer it with doubt')
    )

    blank_doubt_percent = fields.Float(
        string='Blank/doubt percent',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help=('Percentage of times the student did not answer the question or '
              'answer it with doubt')
    )

    blank_wrong = fields.Integer(
        string='Blank/wrong',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help=('Number of times the student did not answer the question or '
              'answer it incorrectly')
    )

    blank_wrong_percent = fields.Float(
        string='Blank/wrong percent',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help=('Percentage of times the student did not answer the question or '
              'answer it incorrectly')
    )

    doubt_wrong = fields.Integer(
        string='Doubt/wrong',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help=('Number of times the student answer the question with doubt '
              'or incorrectly')
    )

    doubt_wrong_percent = fields.Float(
        string='Doubt/wrong percent',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help=('Percentage of times the student answer the question with '
              'doubt or incorrectly')
    )

    blank_doubt_wrong = fields.Integer(
        string='Blank/Doubt/wrong',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help=('Number of times the student did not answer the question, or'
              'answer it with doubt or incorrectly')
    )

    blank_doubt_wrong_percent = fields.Float(
        string='Blank/Doubt/wrong percent',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help=('Percentage of times the student did not answer the question, '
              'or answer it with doubt or incorrectly')
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

    def init(self):
        drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute('''CREATE or REPLACE VIEW {} as (
            {}
        )'''.format(
            self._table,
            ACADEMY_STATISTICS_STUDENT_QUESTION_READONLY_MODEL)
        )

        self.prevent_actions()
