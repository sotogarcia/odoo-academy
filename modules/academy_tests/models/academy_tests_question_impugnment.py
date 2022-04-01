# -*- coding: utf-8 -*-
""" AcademyTestsQuestionImpugnment

This module contains the academy.tests.question.impugnment Odoo model which
stores all student impugnments for questions, their attributes and behavior.
"""

from logging import getLogger

from odoo import models, fields, api
from odoo.tools.translate import _

_logger = getLogger(__name__)


STATES = [
    ('open', 'Opened'),
    ('reply', 'Discuss'),
    ('answer', 'Answered'),
    ('close', 'Closed')
]


class AcademyTestsQuestionImpugnment(models.Model):
    """ Studens can impugn questions, this model stores the impugnment details
    """

    _name = 'academy.tests.question.impugnment'
    _description = u'Academy tests, question impugnment'

    _inherit = ['academy.abstract.owner', 'mail.thread']

    _rec_name = 'name'
    _order = 'write_date DESC, create_date DESC'

    name = fields.Char(
        string='Title',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Short impugnment description',
        size=255,
        translate=True,
        track_visibility='onchange'
    )

    description = fields.Text(
        string='Description',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Long impugnment description',
        translate=True,
        track_visibility='onchange'
    )

    question_id = fields.Many2one(
        string='Question',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Question related with this impugnment',
        comodel_name='academy.tests.question',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        track_visibility='onchange'
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help=('If the active field is set to false, it will allow you to '
              'hide record without removing it')
    )

    student_id = fields.Many2one(
        string='Student',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose student who impugn this question',
        comodel_name='academy.student',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        track_visibility='onchange'
    )

    reply_ids = fields.One2many(
        string='Replies',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.question.impugnment.reply',
        inverse_name='impugnment_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None,
        track_visibility='onchange'
    )

    state = fields.Selection(
        string='State',
        required=True,
        readonly=True,
        index=True,
        default='open',
        help='Display current impugnment state',
        selection=STATES,
        group_expand='_expand_states',
        track_visibility='onchange'
    )

    student_name = fields.Char(
        string='Student name',
        readonly=True,
        related='student_id.res_partner_id.name',
        store=True
    )

    reply_date = fields.Datetime(
        string='Reply date',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Display date of the last reply',
        compute='_compute_reply_date',
        track_visibility='onchange'
    )

    @api.depends('reply_ids')
    def _compute_reply_date(self):
        for record in self:
            if record.reply_ids:
                record.reply_date = record.reply_ids[-1].create_date
            else:
                record.reply_date = None

    _sql_constraints = [
        (
            'description_length',
            'CHECK (char_length(name) >= 3)',
            _(u'The description must be at least three characters long')
        )
    ]

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

    def _has_replies(self):

        self.ensure_one()

        return bool(self.reply_ids)

    def _has_been_answered(self):

        result = False

        self.ensure_one()

        if self._has_replies():
            last_reply = self.reply_ids[-1]

            result = not last_reply.student_id

        return result

    def _update_state(self):

        self.ensure_one()

        if self.state == 'close':
            pass
        elif not self._has_replies():
            self.state = 'open'
        elif self._has_been_answered():
            self.state = 'answer'
        else:
            self.state = 'reply'

    def update_state(self):
        for record in self:
            record._update_state()

    def toggle_open_close(self):
        for record in self:
            if record.state == 'close':
                record.state = None
                record._update_state()
            else:
                record.state = 'close'
