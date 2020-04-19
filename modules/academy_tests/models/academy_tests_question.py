# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" academy tests

This module contains the academy.tests.question an unique Odoo model
which contains all academy tests attributes and behavior.

This model is the representation of the real life question will be used in
one or more tests

Classes:
    AcademyTest: This is the unique model class in this module
    and it defines an Odoo model with all its attributes and related behavior.


TODO:

- [x] Used in view should be shown test information intead of quesition data

"""


from logging import getLogger

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError, UserError


# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)



# pylint: disable=locally-disabled, R0903, W0212
class AcademyTestsQuestion(models.Model):
    """ Questions are the academy testss cornerstone. Each one of the questions
    belongs to a single topic but they can belong to more than one question in
    the selected topic.

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.tests.question'
    _description = u'Academy tests, question'

    _rec_name = 'name'
    _order = 'write_date DESC, create_date DESC'

    _inherit = ['mail.thread']

    # ---------------------------- ENTITY FIELDS ------------------------------

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Text for this question',
        size=1024,
        translate=True,
        track_visibility='onchange'
    )

    preamble = fields.Text(
        string='Preamble',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='What it is said before beginning to question',
        translate=True
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this question',
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

    topic_id = fields.Many2one(
        string='Topic',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Topic to which this question belongs',
        comodel_name='academy.tests.topic',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        track_visibility='onchange',
    )

    category_ids = fields.Many2many(
        string='Categories',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Categories relating to this question',
        comodel_name='academy.tests.category',
        relation='academy_tests_question_category_rel',
        column1='question_id',
        column2='category_id',
        domain=[],
        context={},
        limit=None,
        track_visibility='onchange',
    )

    answer_ids = fields.One2many(
        string='Answers',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Answers will be shown as choice options for this question',
        comodel_name='academy.tests.answer',
        inverse_name='question_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None,
        track_visibility='onchange',
    )

    tag_ids = fields.Many2many(
        string='Tags',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Tag can be used to better describe this question',
        comodel_name='academy.tests.tag',
        relation='academy_tests_question_tag_rel',
        column1='question_id',
        column2='tag_id',
        domain=[],
        context={},
        limit=None,
        track_visibility='onchange',
    )

    level_id = fields.Many2one(
        string='Difficulty',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_level_id(),
        help='Difficulty level of this question',
        comodel_name='academy.tests.level',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        track_visibility='onchange',
    )

    ir_attachment_ids = fields.Many2many(
        string='Attachments',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Attachments needed to solve this question',
        comodel_name='ir.attachment',
        relation='academy_tests_question_ir_attachment_rel',
        column1='question_id',
        column2='attachment_id',
        domain=[],
        context={},
        limit=None,
    )

    test_ids = fields.One2many(
        string='Used in',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Test in which this question has been used',
        comodel_name='academy.tests.test.question.rel',
        inverse_name='question_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None,
    )

    type_id = fields.Many2one(
        string='Type',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose type for this question',
        comodel_name='academy.tests.question.type',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    test_ids = fields.One2many(
        string='Tests',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.test.question.rel',
        inverse_name='question_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None,
    )

    owner_id = fields.Many2one(
        string='Owner',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self._default_owner_id(),
        help='Current question owner',
        comodel_name='res.users',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        groups='academy_base.academy_group_technical'
    )


    # -------------------------- MANAGEMENT FIELDS ----------------------------

    ir_attachment_image_ids = fields.Many2many(
        string='Images',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Images needed to solve this question',
        comodel_name='ir.attachment',
        domain=[('index_content', '=', 'image')],
        context={},
        limit=None,
        compute='_compute_ir_attachment_image_ids',
        search='_search_ir_attachment_image_ids',
    )

    # @api.multi
    @api.depends('ir_attachment_ids')
    def _compute_ir_attachment_image_ids(self):
        for record in self:
            record.ir_attachment_image_ids = record.ir_attachment_ids.filtered(
                lambda r: r.index_content == u'image')


    def _search_ir_attachment_image_ids(self, operator, value):
        error_message = _(('Operation not supported on {}.{}. Only the «Established» and «Not established» '
                           'operators can be used'))

        if operator not in ['=', '!='] or not isinstance(value, bool):
            _logger.warning(error_message.format(self._name, 'ir_attachment_image_ids'))
            return [('id', '=', '-1')]
        else:
            if operator != '=':
                value = not value

            self._cr.execute("""
                SELECT
                    question_id as "id"
                FROM
                    academy_tests_question_ir_attachment_rel AS rel
                INNER JOIN ir_attachment AS ira ON ira."id" = rel.attachment_id
                WHERE ira.index_content = 'image'
            """)

            return [('id', 'in' if value else 'not in', [r[0] for r in self._cr.fetchall()])]


    attachment_count = fields.Integer(
        string='Number of attachments',
        required=False,
        readonly=False,
        index=False,
        default=0,
        help='Number of attachments',
        compute=lambda self: self._compute_attachment_count()
    )

    # @api.multi
    @api.depends('ir_attachment_ids')
    def _compute_attachment_count(self):
        for record in self:
            record.attachment_count = len(record.ir_attachment_ids)

    answer_count = fields.Integer(
        string='Number of answers',
        required=False,
        readonly=False,
        index=False,
        default=0,
        help='Number of answers',
        compute=lambda self: self._compute_answer_count()
    )

    # @api.multi
    @api.depends('answer_ids')
    def _compute_answer_count(self):
        for record in self:
            record.answer_count = len(record.answer_ids)


    category_count = fields.Integer(
        string='Number of categories',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of categories',
        compute=lambda self: self._compute_category_count()
    )

    # @api.multi
    @api.depends('category_ids')
    def _compute_category_count(self):
        for record in self:
            record.category_count = len(record.category_ids)


    # --------------- ONCHANGE EVENTS AND OTHER FIELD METHODS -----------------

    def _default_owner_id(self):
        uid = 1
        if 'uid' in self.env.context:
            uid = self.env.context['uid']

        return uid


    def default_level_id(self):
        """ Computes the level_id default value
        """

        # STEP 1: Set default to none
        level_id = None

        # STEP 2: Search for all levels sorted by sequence
        academy_level_domain = []
        academy_level_obj = self.env['academy.tests.level']
        academy_level_set = academy_level_obj.search(
            academy_level_domain, order="sequence ASC")

        # STEP 3: Gets the middel item from sorted set
        if academy_level_set:
            middle = len(academy_level_set) // 2
            level_id = academy_level_set[middle].id


        return level_id


    @api.onchange('topic_id')
    def _onchange_academy_topid_id(self):
        """ Updates domain form category_ids, this shoud allow categories
        only in the selected topic.
        """
        topic_set = self.topic_id
        valid_ids = topic_set.category_ids & self.category_ids

        self.category_ids = [(6, None, valid_ids.mapped('id'))]


    @api.onchange('ir_attachment_ids')
    def _onchange_ir_attachment_id(self):
        self._compute_ir_attachment_image_ids()


    # -------------------------- PYTHON CONSTRAINS ----------------------------

    @api.constrains('answer_ids', 'name')
    def _check_answer_ids(self):
        """ Check if question have at last one valid answer
        """

        if self.active:
            if not True in self.answer_ids.mapped('is_correct'):
                message = _(u'You must specify at least one correct answer')
                raise ValidationError(message)
            if not False in self.answer_ids.mapped('is_correct'):
                message = _(u'You must specify at least one incorrect answer')
                raise ValidationError(message)


    # ------------------------- OVERWRITTEN METHODS ---------------------------

    @api.model
    def _generate_order_by(self, order_spec, query):
        """ This overwrites order query string using PostgreSQL `RANDOM()`
        method if context variable `sort_by_random` has been set to TRUE.

        This is used by random wizard to select random questions.
        """

        random = self.env.context.get('sort_by_random', False)
        if not random:
            _super = super(AcademyTestsQuestion, self)
            order_str = _super._generate_order_by(order_spec, query)
        else:
            order_str = ' ORDER BY RANDOM() '

        return order_str


    def write(self, values):
        """ When a question is added to a test, active field is set to True
            IMPORTANT: I don't know why Odoo performs this action
            This method allows to users who have no access rights to link
            questions to tests
        """

        if len(values.keys()) == 1 and 'active' in values.keys():
            result = super(AcademyTestsQuestion, self.sudo()).write(values)
        else:
            result = super(AcademyTestsQuestion, self).write(values)

        return result
