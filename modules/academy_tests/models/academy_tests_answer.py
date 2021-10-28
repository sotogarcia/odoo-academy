# -*- coding: utf-8 -*-
""" AcademyTestsAnswer

This module contains the academy.tests.answer Odoo model which stores
all academy tests answer attributes and behavior.
"""

from logging import getLogger

from odoo import models, fields
from odoo.tools.translate import _

_logger = getLogger(__name__)


class AcademyTestsAnswer(models.Model):
    """ This model stores an answer for existing academy.tests.question
    """

    _name = 'academy.tests.answer'
    _description = u'Academy tests, question answer'

    _rec_name = 'name'
    _order = 'sequence ASC, id ASC'

    _inherit = ['academy.abstract.spreadable', 'mail.thread']

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
            'target': 'current',
            'state': 'paid'
        }

    def _track_subtype(self, init_values):
        self.ensure_one()

        if('active' not in init_values):
            xid = 'academy_tests.academy_tests_answer_written'
            return self.env.ref(xid)
        else:
            _super = super(AcademyTestsAnswer, self)
            return _super._track_subtype(init_values)

    def _spread_to(self, subtype_id=False, subtype=None):
        expected = 'academy_tests.academy_tests_answer_written'

        result = []
        self.ensure_one()

        if subtype_id == self.env.ref(expected).id:
            result.append(self.question_id)

        return result
