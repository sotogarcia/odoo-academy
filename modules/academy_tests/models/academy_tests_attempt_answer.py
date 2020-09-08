# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


def _made_check():
    case1 = '("user_action" = \'blank\' and "answer_id" IS NULL)'
    case2 = '("user_action" <> \'blank\' and "answer_id" IS NOT NULL)'

    return 'CHECK({} or {})'.format(case1, case2)


class AcademyTestsAttemptAnswer(models.Model):
    """ Logs all student answers in a test attempt, even if later he
    change it by another answer
    """

    _name = 'academy.tests.attempt.answer'
    _description = u'Academy tests attempt answer'

    _rec_name = 'id'
    _order = 'instant ASC'


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
        string='Question',
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
        selection=[
            ('blank', 'Leave blank'),
            ('doubt', 'Doubt'),
            ('answer', 'Answer'),
        ]
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
