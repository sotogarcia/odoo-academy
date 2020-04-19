# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" academy tests

This module contains the academy.tests.answer an unique Odoo model
which contains all academy tests answer attributes and behavior.

This model is the representation of the real life answer for question

Classes:
    AcademyTest: This is the unique model class in this module
    and it defines an Odoo model with all its attributes and related behavior.

"""


from logging import getLogger

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.tools.translate import _


# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)



# pylint: disable=locally-disabled, R0903
class AcademyTestsAnswer(models.Model):
    """ Answer for a question

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.tests.answer'
    _description = u'Academy tests, question answer'

    _rec_name = 'name'
    _order = 'sequence ASC, id ASC'

    _inherit = ['mail.thread']

    # ---------------------------- ENTITY FIELDS ------------------------------

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Text for this answer',
        size=1024,
        translate=True
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
              'hide record without removing it')
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
        # oldname='academy_question_id'
    )

    is_correct = fields.Boolean(
        string='Is correct?',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Checked means this is a right answer for the question'
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

    # @api.multi
    def cmd_open_in_form(self):
        return {
            'name': 'Answers',
            # 'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'academy.tests.answer',
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'current',
            'state': 'paid'
        }
