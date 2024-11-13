# -*- coding: utf-8 -*-
""" AcademyTestsAnswer

This module contains the academy.tests.answer Odoo model which stores
all academy tests answer attributes and behavior.
"""

from logging import getLogger

from odoo import models, fields, api
from odoo.tools.translate import _

_logger = getLogger(__name__)


class AcademyTestsAnswer(models.Model):
    """ This model stores an answer for existing academy.tests.question
    """

    _name = 'academy.tests.answer'
    _description = u'Academy tests, question answer'

    _rec_name = 'name'
    _order = 'sequence ASC, id ASC'

    _inherit = ['mail.thread']

    # ---------------------------- ENTITY FIELDS ------------------------------

    name = fields.Char(
        string='Answer',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Text for this answer',
        size=1024,
        translate=True,
        track_visibility='onchange'
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this topic',
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help=('If the active field is set to false, it will allow you to '
              'hide record without removing it'),
        track_visibility='onchange'
    )

    question_id = fields.Many2one(
        string='Question',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Question to which this answer belongs',
        comodel_name='academy.tests.question',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
    )

    is_correct = fields.Boolean(
        string='Is correct?',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Checked means this is a right answer for the question',
        track_visibility='onchange'
    )

    sequence = fields.Integer(
        string='Sequence',
        required=True,
        readonly=False,
        index=False,
        default=10,
        help='Preference order for this answer'
    )

    # --------------------------- SQL_CONTRAINTS ------------------------------

    _sql_constraints = [
        (
            'answer_by_question_uniq',
            'UNIQUE(name, question_id)',
            _(u'There is already another answer with the same text')
        )
    ]

    # --------------------------- PUBLIC METHODS ------------------------------

    def cmd_open_in_form(self):
        return {
            'name': 'Answers',
            "view_mode": 'form',
            'res_model': 'academy.tests.answer',
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
            'state': 'paid'
        }

    @api.model_create_multi
    def create(self, vals_list):
        records = super(AcademyTestsAnswer, self).create(vals_list)

        for record in records:
            record.message_change_thread(record.question_id)

        return records

    def write(self, values):
        result = super(AcademyTestsAnswer, self).write(values)

        for record in self:
            record.message_change_thread(record.question_id)

        return result
