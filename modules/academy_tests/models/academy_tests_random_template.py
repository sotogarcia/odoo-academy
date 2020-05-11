# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" Academy Tests Random Wizard Set

This module contains the academy.tests.random.wizard.Set an unique Odoo model
which contains all Academy Tests Random Wizard Set attributes and behavior.

This model is the representation of the real life academy tests random template

Classes:
    AcademyTestsRandomWizardSet: This is the unique model class in this module
    and it defines an Odoo model with all its attributes and related behavior.

    Inside this class can be, in order, the following attributes and methods:
    * Object attributes like name, description, inheritance, etc.
    * Entity fields with the full definition
    * Computed fields and required computation methods
    * Events (@api.onchange) and other field required methods like computed
    domain, defaul values, etc...
    * Overloaded object methods, like create, write, copy, etc.
    * Public object methods will be called from outside
    * Private auxiliary methods not related with the model fields, they will
    be called from other class methods


Todo:
    * Complete the model attributes and behavior

"""


from logging import getLogger

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.tools.translate import _


# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)



# pylint: disable=locally-disabled, R0903
class AcademyTestsRandomTemplate(models.Model):
    """ This model is the representation of the academy tests random template

    Fields:
      name (Char)       : Human readable name which will identify each record
      description (Text): Something about the record or other information which
      has not an specific defined field to store it.
      active (Boolean)  : Checked do the record will be found by search and
      browse model methods, unchecked hides the record.

    """


    _name = 'academy.tests.random.template'
    _description = u'Academy Tests Random Template'

    _inherit = ['image.mixin', 'mail.thread']

    _rec_name = 'name'
    _order = 'name ASC'


    name = fields.Char(
        string='Name',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Enter new name',
        size=255,
        translate=True,
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Enter new description',
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Enables/disables the record'
    )

    random_line_ids = fields.One2many(
        string='Lines',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.random.line',
        inverse_name='random_template_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    test_ids = fields.One2many(
        string='Used in',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.test',
        inverse_name='random_template_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )


    owner_id = fields.Many2one(
        string='Owner',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_owner_id(),
        help='Current test owner',
        comodel_name='res.users',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        groups='academy_base.academy_group_technical'
    )

    quantity = fields.Integer(
        string='Quantity',
        required=True,
        readonly=False,
        index=False,
        default=0,
        help='Maximum number of questions can be appended',
        compute='compute_quantity'
    )


    lines_count = fields.Integer(
        string='Nº lines',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of lines',
        store=False,
        compute='compute_line_count'
    )


    # ----------------- AUXILIARY FIELDS METHODS AND EVENTS -------------------


    def default_owner_id(self):
        uid = 1
        if 'uid' in self.env.context:
            uid = self.env.context['uid']

        return uid


    @api.depends('random_line_ids')
    def compute_quantity(self):
        """ This computes lines_count field """
        for record in self:
            values = record.random_line_ids.mapped('quantity')
            record.quantity = sum(values)


    @api.depends('random_line_ids')
    def compute_line_count(self):
        """ This computes lines_count field """
        for record in self:
            record.lines_count = len(record.random_line_ids)


    # -------------------------- AUXILIARY METHODS ----------------------------


    def _compute_base_sequence_value(self, test_id):
        """ Get the greater sequence value of the set of questions in test
        and returns it. If there are no questions the returned value will be 0

        @note: this is not a ordinary compute method
        @note: next sequence must be ``returned value + 1``
        """

        sequences = test_id.question_ids.mapped('sequence') or [0]
        return (max(sequences)) + 0


    def _get_base_values(self, test_id, sequence):
        """ Builds a dictionary with the required values to create a new
        ``academy.tests.test.question.rel`` record, this will act as a link
        between given test and future question
        """

        return {
            'test_id': test_id.id,
            'question_id': None,
            'sequence': sequence,
            'active': True
        }


    @staticmethod
    def _build_many2many_write_action(question_set, base_values):
        leafs = []
        values = base_values.copy()
        for question in question_set:
            values['question_id'] = question.id
            values['sequence'] = values['sequence'] + 1

            leafs.append((0, None, values.copy()))

        return leafs


    def _perform_many2many_write_action(self, leafs, test_id):
        return test_id.write({'question_ids': leafs})


    # ---------------------------- PUBIC METHODS ------------------------------

    def append_questions(self, test_id, overwrite=False):
        """ Calls action by each related line
        """

        self.ensure_one()

        result_set = self.env['academy.tests.question']

        if overwrite:
            test_id.write({'question_ids': [(5, 0, 0)]})

        for line in self.random_line_ids:

            # STEP 1: build skeeton dictionary with required values to create
            # new ``academy.tests.test.question.rel`` records
            sequence = self._compute_base_sequence_value(test_id)
            values = self._get_base_values(test_id, sequence)

            # STEP 2: build a domain to exclude existing questions
            # NOTE: Questions are linked to ``academy.tests.test.question.rel``
            exclusion_leafs = []
            if test_id.question_ids:
                qids = test_id.question_ids.mapped('question_id').mapped('id')
                exclusion_leafs.append(('id', 'not in', qids))

            # STEP 3: Performa search and return a set of questions
            question_set = line.perform_search(exclusion_leafs)

            # STEP 4: Link questions through many2many relation
            leafs = self._build_many2many_write_action(question_set, values)
            self._perform_many2many_write_action(leafs, test_id)

            # STEP 5: Accumulate questions in result set
            result_set += question_set

        return result_set
