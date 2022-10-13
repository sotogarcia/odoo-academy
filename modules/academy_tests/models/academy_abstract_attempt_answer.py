# -*- coding: utf-8 -*-
""" AcademyTestsAttemptAnswer

This module contains the academy.tests.attempt.answer Odoo model which stores
all academy tests attempt answer attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger

_logger = getLogger(__name__)


USER_ACTIONS = [
    ('blank', 'Blank answer'),
    ('doubt', 'Unsure answer'),
    ('answer', 'Sure answer'),
]


def _made_check():
    case1 = '("user_action" = \'blank\' and "answer_id" IS NULL)'
    case2 = '("user_action" <> \'blank\' and "answer_id" IS NOT NULL)'

    return 'CHECK({} or {})'.format(case1, case2)


class AcademyAbstractAttemptAnswer(models.AbstractModel):
    """ Logs all student answers in a test attempt, even if later he
    change it by another answer
    """

    _name = 'academy.abstract.attempt.answer'
    _description = u'Academy tests attempt answer'

    _rec_name = 'id'
    _order = 'instant DESC'

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Check it to show this attempt or uncheck to archivate'
    )

    attempt_id = fields.Many2one(
        string='Attempt',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose the attempt which is being done',
        comodel_name='academy.tests.attempt',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    question_link_id = fields.Many2one(
        string='Question link',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Question that has been answered',
        comodel_name='academy.tests.test.question.rel',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    answer_id = fields.Many2one(
        string='Answer',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose the answer which has been selected by user',
        comodel_name='academy.tests.answer',
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

    user_action = fields.Selection(
        string='User action',
        required=True,
        readonly=False,
        index=False,
        default='blank',
        help='What did the user do?',
        selection=USER_ACTIONS
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
        auto_join=False,
        related='question_link_id.question_id'
    )

    _sql_constraints = [
        (
            'check_blank_answer',
            _made_check(),
            _(u'Field answer_id is mandatory except for blanks')
        )
    ]

    @api.onchange('attempt_id')
    def _onchange_attempt_id(self):
        test_id = self.attempt_id.test_id
        return {
            'domain': {
                'question_link_id': [('test_id', '=', test_id.id)]
            }
        }

    @api.onchange('question_link_id')
    def _onchange_question_link_id(self):
        question_id = self.question_link_id.question_id

        return {
            'domain': {
                'answer_id': [('question_id', '=', question_id.id)]
            }
        }

    @api.onchange('user_action')
    def _onchange_user_action(self):
        for record in self:
            if record.user_action == 'blank':
                record.answer_id = None

    @api.depends('answer_id', 'user_action')
    def name_get(self):
        result = []
        for record in self:
            if isinstance(record.id, models.NewId):
                name = _('New attempt answer')
            else:
                answer = record.answer_id.name or _('Answer')
                action = record.user_action or _('Blank')
                name = '{} - {} - #{}'.format(answer, action, record.id)

            result.append((record.id, name))

        return result

    def write(self, values):
        """ Remove answer_id when user action is True
        """

        user_action = values.get('user_action', False)
        if user_action == 'blank':
            values['answer_id'] = None

        result = super(AcademyAbstractAttemptAnswer, self).write(values)

        return result
