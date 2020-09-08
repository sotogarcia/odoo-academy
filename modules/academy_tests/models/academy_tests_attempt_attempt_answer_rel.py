# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools import drop_view_if_exists
from logging import getLogger
from .lib.libuseful import ACADEMY_TESTS_ATTEMPT_ATTEMPT_ANSWER_REL


_logger = getLogger(__name__)


class AcademyTestsAttemptAttemptAnswerRel(models.Model):
    """ Builds a view with all finally attempt answers. This view will
    be used as middle table in many2many field to show final attempt
    answers by attempt.

    Only the following fields: attempt_id and attempt_answer_id, are
    required, all other can be usefull in a future.
    """

    _name = 'academy.tests.attempt.attempt.answer.rel'
    _description = u'Academy tests attempt attempt answer rel'

    _rec_name = 'attempt_id'
    _order = 'attempt_id ASC, sequence ASC'

    _auto = False

    _table = 'academy_tests_attempt_attempt_answer_rel'


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
        drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute('''CREATE or REPLACE VIEW {} as (
            {}
        )'''.format(
            self._table,
            ACADEMY_TESTS_ATTEMPT_ATTEMPT_ANSWER_REL)
        )
