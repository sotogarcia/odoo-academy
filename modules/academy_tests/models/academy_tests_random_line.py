# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" Academy Tests Random Wizard Line

This module contains the academy.tests.random.line. an unique Odoo model
which contains all Academy Tests Random Wizard Line  attributes and behavior.

"""


from logging import getLogger
from datetime import datetime

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.tools.translate import _


# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)


WIZARD_LINE_STATES = [
    ('step1', 'General'),
    ('step2', 'Topics/Categories'),
    ('step3', 'Tests'),
    ('step4', 'Questions')
]

# in question, in this line, exclude/include
FIELD_MAPPING = [
    ('type_id', 'type_ids', 'exclude_types'),
    ('id', 'test_ids.question_ids', 'exclude_tests'),
    ('topic_id', 'topic_ids', 'exclude_topics'),
    ('category_ids', 'category_ids', 'exclude_categories'),
    ('tag_ids', 'tag_ids', 'exclude_tags'),
    ('level_id', 'level_ids', 'exclude_levels'),
    ('id', 'question_ids', 'exclude_questions'),
]


# pylint: disable=locally-disabled, R0903, W0212
class AcademyTestsRandomWizardLine(models.Model):
    """ This model is the representation of the academy tests random line

    Fields:
      name (Char)       : Human readable name which will identify each record
      description (Text): Something about the record or other information which
      has not an specific defined field to store it.
      active (Boolean)  : Checked do the record will be found by search and
      browse model methods, unchecked hides the record.

    """


    _name = 'academy.tests.random.line'
    _description = u'Academy tests, random line'


    _rec_name = 'name'
    _order = 'sequence ASC, name ASC'


    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self.default_name(),
        help="Name for this line",
        size=255,
        translate=True,
        track_visibility='onchange'
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this line',
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

    sequence = fields.Integer(
        string='Sequence',
        required=True,
        readonly=False,
        index=False,
        default=10,
        help=('Place of this line in the order of the lines from parent')
    )

    state = fields.Selection(
        string='State',
        required=True,
        readonly=False,
        index=False,
        default='step1',
        help=False,
        selection=WIZARD_LINE_STATES
    )

    random_template_id = fields.Many2one(
        string='Template',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.random.template',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    quantity = fields.Integer(
        string='Quantity',
        required=True,
        readonly=False,
        index=False,
        default=20,
        help='Maximum number of questions can be appended'
    )

    type_ids = fields.Many2many(
        string='Types',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.question.type',
        relation='academy_tests_random_line_question_type_rel',
        column1='random_line_id',
        column2='type_id',
        domain=[],
        context={},
        limit=None
    )

    exclude_types = fields.Boolean(
        string='Exclude selected types',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to disallow selected records instead allow them'
    )

    disallow_attachments = fields.Boolean(
        string='Disallow all attachments',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to exclude all questions have attachments'
    )

    test_ids = fields.Many2many(
        string='Tests',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose allowed tests or leave empty to allow all',
        comodel_name='academy.tests.test',
        relation='academy_tests_random_line_test_rel',
        column1='random_line_id',
        column2='test_id',
        domain=[],
        context={},
        limit=None
    )

    exclude_tests = fields.Boolean(
        string='Exclude selected tests',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to disallow selected records instead allow them'
    )

    topic_ids = fields.Many2many(
        string='Topics',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose allowed topics or leave empty to allow all',
        comodel_name='academy.tests.topic',
        relation='academy_tests_random_line_topic_rel',
        column1='random_line_id',
        column2='topic_id',
        domain=[],
        context={},
        limit=None
    )

    exclude_topics = fields.Boolean(
        string='Exclude selected topics',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to disallow selected records instead allow them'
    )

    category_ids = fields.Many2many(
        string='Categories',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose allowed categories or leave empty to allow all',
        comodel_name='academy.tests.category',
        relation='academy_tests_random_line_category_rel',
        column1='random_line_id',
        column2='category_id',
        domain=[],
        context={},
        limit=None
    )

    exclude_categories = fields.Boolean(
        string='Exclude selected categories',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it this to disallow selected records instead allow them'
    )

    tag_ids = fields.Many2many(
        string='Labels',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose allowed tags or leave empty to allow all',
        comodel_name='academy.tests.tag',
        relation='academy_tests_random_line_tag_rel',
        column1='random_line_id',
        column2='tag_id',
        domain=[],
        context={},
        limit=None
    )

    exclude_tags = fields.Boolean(
        string='Exclude selected tags',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to disallow selected records instead allow them'
    )

    level_ids = fields.Many2many(
        string='Levels',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose allowed levels or leave empty to allow all',
        comodel_name='academy.tests.level',
        relation='academy_tests_random_line_level_rel',
        column1='random_line_id',
        column2='level_id',
        domain=[],
        context={},
        limit=None
    )

    exclude_levels = fields.Boolean(
        string='Exclude selected levels',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to disallow selected records instead allow them'
    )

    question_ids = fields.Many2many(
        string='Questions',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose allowed questions or leave empty to allow all',
        comodel_name='academy.tests.question',
        relation='academy_tests_random_line_question_rel',
        column1='random_line_id',
        column2='question_id',
        domain=[],
        context={},
        limit=None
    )

    exclude_questions = fields.Boolean(
        string='Exclude selected questions',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it this to disallow selected records instead allow them'
    )


    # ----------------------- AUXILIARY FIELD METHODS -------------------------

    def default_name(self):
        """ Computes default value for name
        """
        current_time = datetime.now()
        return fields.Datetime.context_timestamp(self, timestamp=current_time)


    # -------------------------- MANAGEMENT FIELDS ----------------------------

    type_count = fields.Integer(
        string='Nº types',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of types',
        store=False,
        compute='compute_type_count'
    )

    @api.depends('type_ids', 'exclude_types')
    def compute_type_count(self):
        """ This computes type_count field """
        for record in self:
            sign = -1 if record.exclude_types else 1
            record.type_count = len(record.type_ids) * sign

    test_count = fields.Integer(
        string='Nº tests',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of tests',
        store=False,
        compute='compute_test_count'
    )

    @api.depends('test_ids', 'exclude_tests')
    def compute_test_count(self):
        """ This computes test_count field """
        for record in self:
            sign = -1 if record.exclude_tests else 1
            record.test_count = len(record.test_ids) * sign

    topic_count = fields.Integer(
        string='Nº topics',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of topics',
        store=False,
        compute='compute_topic_count'
    )

    @api.depends('topic_ids', 'exclude_topics')
    def compute_topic_count(self):
        """ This computes topic_count field """
        for record in self:
            sign = -1 if record.exclude_topics else 1
            record.topic_count = len(record.topic_ids) * sign

    category_count = fields.Integer(
        string='Nº categories',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of categories',
        store=False,
        compute='compute_category_count'
    )

    @api.depends('category_ids', 'exclude_categories')
    def compute_category_count(self):
        """ This computes category_count field """
        for record in self:
            sign = -1 if record.exclude_categories else 1
            record.category_count = len(record.category_ids) * sign

    tag_count = fields.Integer(
        string='Nº tags',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of tags',
        store=False,
        compute='compute_tag_count'
    )

    @api.depends('tag_ids', 'exclude_tags')
    def compute_tag_count(self):
        """ This computes tag_count field """
        for record in self:
            sign = -1 if record.exclude_tags else 1
            record.tag_count = len(record.tag_ids) * sign

    level_count = fields.Integer(
        string='Nº levels',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of levels',
        store=False,
        compute='compute_level_count'
    )

    @api.depends('level_ids', 'exclude_levels')
    def compute_level_count(self):
        """ This computes level_count field """
        for record in self:
            sign = -1 if record.exclude_levels else 1
            record.level_count = len(record.level_ids) * sign

    question_count = fields.Integer(
        string='Nº questions',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of questions',
        store=False,
        compute='compute_question_count'
    )

    @api.depends('question_ids', 'exclude_questions')
    def compute_question_count(self):
        """ This computes question_count field """
        for record in self:
            sign = -1 if record.exclude_questions else 1
            record.question_count = len(record.question_ids) * sign


    # --------------------------- PRIVATE METHODS -----------------------------

    def _reload_on_step1(self):
        """ Builds an action which loads again transient model record using
        'step3' as state
        @note: actually this method is not used
        """
        self.write({'state': 'step1'})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'academy.tests.random.line',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new'
        }


    @staticmethod
    def _domain_item(leaf, ids, exclude):
        """ Builds a domain leaf. All leafs created by this method will be
        `in` or `not in`.

        @param leaf (string): realational field name
        @param ids (list): list of ids to include or exclude
        @param exclude (bool): True to use `not in` or False to use `in`
        """

        if ids:
            operator = 'not in' if exclude else 'in'
            return (leaf, operator, ids)

        return None


    def _get_ids(self, field_path):
        """This gets ids from given relational field set, this can be
        referred by a single field name or by dots separated field path.

        @param field_path (string): field names separated by dots, like:
        test_ids.question_ids
        @return (list): list of ids in set
        """
        result = self

        for step in field_path.split('.'):
            result = result.mapped(step)

        return result.mapped('id')

    # --------------------------- PUBLIC METHODS ------------------------------

    def get_leafs(self):
        """ Walk over field mapping making domain leafs for each of those that
         have been set.

        @note: FIELD_MAPPING has been defined at the top of this module, it's
        a list of items like: ('type_id', 'type_ids', 'exclude_types')

        @return (list): list of domain leafs without ampersand
        """

        self.ensure_one()

        leafs = []
        for field_map in FIELD_MAPPING:
            leaf = field_map[0]
            ids = self._get_ids(field_map[1])
            exclude = getattr(self, field_map[2])
            ditem = self._domain_item(leaf, ids, exclude)
            if ditem:
                leafs.append(ditem)

        if self.disallow_attachments:
            leafs.append(('ir_attachment_ids', '=', False))

        return leafs


    def get_domain(self, extra_leafs=None):
        """ Search for questions to append
        """

        self.ensure_one()

        domain = self.get_leafs()
        if extra_leafs:
            domain = domain + extra_leafs

        if len(domain) > 1:
            domain = ['&'] + domain

        msg = _('Domain {} will be used to append random questions')
        _logger.info(msg.format(domain))

        return domain


    def perform_search(self, extra_leafs=None):
        """ Reads values from each line in recordset, performs search and
        returns question ids

        @param extra_leafs: list with extra leafs to be append to domain
        """

        # STEP1: Create an empty question recordset with random sort context
        ctx = {'sort_by_random': True}
        question_set = self.env['academy.tests.question'].with_context(ctx)

        # STEP2: Ensure extra_leafs is a list
        extra_leafs = extra_leafs or []

        for record in self:

            # STEP3: Merge extra_leafs with a new leaf witch excludes current
            # accumulate questions
            exclusion_leafs = extra_leafs
            if question_set:
                qids = question_set.mapped('question_id')
                exclusion_leafs.append(('id', 'not in', qids))

            # STEP 4: Build domain with line values and merge exclusion leafs
            domain = record.get_domain(exclusion_leafs)

            # STEP 5: Perform search and append to previouly created recordset
            question_set += question_set.search(domain, limit=record.quantity)

        return question_set
