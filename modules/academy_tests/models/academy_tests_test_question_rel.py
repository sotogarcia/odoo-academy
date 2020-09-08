# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" academy tests

This module contains the academy.tests.test.question.rel an unique Odoo model
which contains all academy tests attributes and behavior.

This model is the representation of the middle many to may relationship
between test and question, this additionally stores sequence order

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
class AcademyTestsTestQuestionRel(models.Model):
    """ The summary line for a class docstring should fit on one line.

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.tests.test.question.rel'
    _description = u'Academy tests, test-question relationship'

    _inherits = {
        'academy.tests.question': 'question_id'
    }

    _rec_name = 'test_id'
    _order = 'sequence ASC, id ASC'

    test_id = fields.Many2one(
        string='Test',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Test to which this item belongs',
        comodel_name='academy.tests.test',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        # oldname='academy_test_id'
    )

    question_id = fields.Many2one(
        string='Question',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Question will be related with test',
        comodel_name='academy.tests.question',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        # oldname='academy_question_id'
    )

    sequence = fields.Integer(
        string='Sequence',
        required=False,
        readonly=False,
        index=False,
        default=0,
        help='Question sequence order'
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help=('If the active field is set to false, it will allow you to '
              'hide record without removing it'),
        related='question_id.active',
        store=True
    )


    _sql_constraints = [
        (
            'prevent_duplicate_questions',
            'UNIQUE (test_id, question_id)',
            _(u'Duplicate question in test')
        )
    ]


    def name_get(self):
        result = []

        for record in self:
            if self.env.context.get('show_question_id', False):
                result.append((record.id, record.question_id.name))
            else:
                result.append((record.id, record.test_id.name))

        return result
