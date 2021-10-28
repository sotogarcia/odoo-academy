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
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Test to which this item belongs',
        comodel_name='academy.tests.test',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
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

    # This only is used by 'view_academy_tests_test_question_rel_form' view
    perform = fields.Selection(
        string='Perform',
        required=False,
        readonly=False,
        index=False,
        default='link',
        help='Choose how the new link will be created',
        selection=[
            ('link', 'Link an existing question'),
            ('new', 'Create a new question')
        ]
    )

    index = fields.Integer(
        string='Index',
        required=False,
        readonly=True,
        index=False,
        default=1,
        help='Show the order of the question in the test',
        related="sequence",
        store=False
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

    def switch_status(self):
        """ This method is only a wrapper will be allows user to call
        the real switch_status existing in related question
        """

        question_ids = self.mapped('question_id')
        question_ids.switch_status()

    def _is_a_new_question(values):
        keys = values.keys()
        result = 'question_id 'not in keys
        result = result and 'name' in keys
        result = result and 'topic_id' in keys
        result = result and 'topic_version_ids' in keys
        result = result and 'category_ids' in keys
        result = result and 'type_id' in keys
        result = result and 'level_id' in keys
        result = result and 'owner_id' in keys
        result = result and 'answer_ids' in keys

        return result

    def _get_text_id(self, values):
        test_id = values.get('test_id')

        if not test_id:
            active_model = self.env.context.get('active_model', False)
            active_id = self.env.context.get('active_id', False)

            if active_model == 'academy.tests.test' and active_id:
                test_id = active_id

        return test_id

    @api.model
    def create(self, values):
        """
            Create a new record for a model ModelName
            @param values: provides a data for new record

            @return: returns a id of new record
        """

        test_id = self._get_text_id(values)

        if test_id:
            link_obj = self.env['academy.tests.test.question.rel']
            link_set = link_obj.search([('test_id', '=', test_id)])
            sequences = link_set.mapped('sequence') or [0]
            values['sequence'] = max(sequences) + 1

        if 'question_id' not in values and 'name' in values:
            temp = values.copy()
            question_values = values.copy()

            question_values.pop('test_id')
            question_values.pop('sequence')

            question_item = self.env['academy.tests.question']
            question_item.create(question_values)

            values = {
                'test_id': temp.get('test_id', None),
                'question_id': question_item.id,
                'sequence': temp.get('sequence', 1)
            }

        _super = super(AcademyTestsTestQuestionRel, self)
        result = _super.create(values)

        return result
