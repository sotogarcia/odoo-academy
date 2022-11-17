# -*- coding: utf-8 -*-
""" AcademyTestsQuestion

This module contains the academy.tests.question Odoo model which stores
all academy tests question attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError, UserError
from odoo.osv.expression import FALSE_DOMAIN, TRUE_DOMAIN

from logging import getLogger
from os import linesep
from re import search, UNICODE, IGNORECASE
from enum import Enum

from .utils.libuseful import prepare_text, fix_established, is_numeric

from .utils.sql_operations import FIND_MOST_USED_QUESTION_FIELD_VALUE_FOR_SQL
from .utils.sql_operations import FIND_MOST_USED_QUESTION_CATEGORY_VALUE_SQL
from .utils.sql_inverse_searches import SEARCH_IS_UNCATEGORIZED

from .utils.sql_inverse_searches import ANSWER_COUNT_SEARCH

_logger = getLogger(__name__)


class Mi(Enum):
    """ Enumerates regex group index un line processing
    """
    ALL = 0
    QUESTION = 1
    ANSWER = 2
    LETTER = 3
    FALSE = 4
    TRUE = 5
    DESCRIPTION = 6
    IMAGE = 7
    TITLE = 8
    URI = 9
    CONTENT = 10


class AcademyTestsQuestion(models.Model):
    """ Questions are the academy testss cornerstone. Each one of the questions
    belongs to a single topic but they can belong to more than one question in
    the selected topic.
    """

    _name = 'academy.tests.question'
    _description = u'Academy tests, question'

    _rec_name = 'name'
    _order = 'write_date DESC, create_date DESC'

    _inherit = [
        'ownership.mixin',
        'mail.thread',
        'mail.activity.mixin'
    ]

    # ---------------------------- ENTITY FIELDS ------------------------------

    name = fields.Char(
        string='Statement',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Text for this question',
        size=1024,
        translate=True,
        tracking=True
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
        index=True,
        default=True,
        help=('If the active field is set to false, it will allow you to '
              'hide record without removing it')
    )

    topic_id = fields.Many2one(
        string='Topic',
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self.default_topic_id(),
        help='Topic to which this question belongs',
        comodel_name='academy.tests.topic',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        tracking=True,
    )

    version_ids = fields.Many2many(
        string='Versions',
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self.default_version_ids(),
        help='Choose which versions of the topic this question belongs to',
        comodel_name='academy.tests.version',
        relation='academy_tests_question_version_rel',
        column1='question_id',
        column2='version_id',
        domain=[],
        context={},
        limit=None,
        tracking=True
    )

    category_ids = fields.Many2many(
        string='Categories',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Categories relating to this question',
        comodel_name='academy.tests.category',
        relation='academy_tests_question_category_rel',
        column1='question_id',
        column2='category_id',
        domain=[],
        context={},
        limit=None,
        tracking=True,
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
        copy=True
    )

    tag_ids = fields.Many2many(
        string='Tags',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Tag can be used to better describe this question',
        comodel_name='academy.tests.tag',
        relation='academy_tests_question_tag_rel',
        column1='question_id',
        column2='tag_id',
        domain=[],
        context={},
        limit=None,
        tracking=True,
    )

    level_id = fields.Many2one(
        string='Difficulty',
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self.default_level_id(),
        help='Difficulty level of this question',
        comodel_name='academy.tests.level',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        tracking=True,
    )

    ir_attachment_ids = fields.Many2many(
        string='Attachments',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Attachments needed to solve this question',
        comodel_name='ir.attachment',
        relation='academy_tests_question_ir_attachment_rel',
        column1='question_id',
        column2='attachment_id',
        domain=[('res_model', '=', False), ('public', '=', True)],
        context={
            'tree_view_ref': 'academy_tests.view_ir_attachment_tree',
            'form_view_ref': 'academy_tests.view_ir_attachment_form',
            'search_view_ref': 'academy_tests.view_attachment_search',
            'search_default_my_documents_filter': 0,
            'search_default_my_own_documents_filter': 1
        },
        limit=None,
    )

    type_id = fields.Many2one(
        string='Type',
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self.default_type_id(),
        help='Choose type for this question',
        comodel_name='academy.tests.question.type',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    link_ids = fields.One2many(
        string='Used in',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Test in which this question has been used',
        comodel_name='academy.tests.test.question.rel',
        inverse_name='question_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None,
    )

    status = fields.Selection(
        string='State',
        required=True,
        readonly=False,
        index=True,
        default='ready',
        help='Current question status',
        selection=[
            ('draft', 'Draft'),
            ('ready', 'Ready')
        ],
        tracking=True
    )

    authorship = fields.Boolean(
        string='Authorship',
        required=False,
        readonly=False,
        index=True,
        default=True,
        help='Check it to indicate that it is your own authorship'
    )

    depends_on_id = fields.Many2one(
        string='Direct dependency',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Choose the question on which it depends',
        comodel_name='academy.tests.question',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    depends_on_ids = fields.Many2manyView(
        string='Depends on',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help=False,
        comodel_name='academy.tests.question',
        relation='academy_tests_question_dependency_rel',
        column1='question_id',
        column2='depends_on_id',
        domain=[],
        context={},
        limit=None,
    )

    dependent_ids = fields.Many2manyView(
        string='Dependents',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help=False,
        comodel_name='academy.tests.question',
        relation='academy_tests_question_dependency_rel',
        column1='depends_on_id',
        column2='question_id',
        domain=[],
        context={},
        limit=None,
    )

    # -------------------------- MANAGEMENT FIELDS ----------------------------

    color = fields.Integer(
        string='Color Index',
        required=True,
        readonly=True,
        index=False,
        default=10,
        help='Display color based on dependency and status',
        store=False,
        compute='_compute_color'
    )

    def _compute_color(self):
        for record in self:
            if record.status == 'draft':
                record.color = 1
            elif record.depends_on_id:
                record.color = 3
            else:
                record.color = 10

    dependency_count = fields.Integer(
        string='Dependencies',
        required=False,
        readonly=False,
        index=False,
        default=0,
        help='Number of attachments',
        store=False,
        compute='_compute_dependency_count'
    )

    @api.depends('depends_on_ids')
    def _compute_dependency_count(self):
        for record in self:
            record.dependency_count = len(record.depends_on_ids)

    dependent_count = fields.Integer(
        string='Number of dependents',
        required=False,
        readonly=False,
        index=False,
        default=0,
        help='Number of attachments',
        store=False,
        compute='_compute_dependent_count'
    )

    @api.depends('dependent_ids')
    def _compute_dependent_count(self):
        for record in self:
            record.dependent_count = len(record.dependent_ids)

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
        search='_search_ir_attachment_image_ids'
    )

    @api.depends('ir_attachment_ids')
    def _compute_ir_attachment_image_ids(self):
        for record in self:
            record.ir_attachment_image_ids = record.ir_attachment_ids.filtered(
                lambda r: r.index_content == u'image')

    def _search_ir_attachment_image_ids(self, operator, value):
        message = _(('Operation not supported on {}.{}. ',
                     'Only the «Established» and «Not established» '
                     'operators can be used'))

        if operator not in ['=', '!='] or not isinstance(value, bool):
            msg = message.format(self._name, 'ir_attachment_image_ids')
            _logger.info(msg)
            return FALSE_DOMAIN
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

            op = 'in' if value else 'not in'
            ids = [r[0] for r in self._cr.fetchall()]

            return [('id', op, ids)]

    ir_attachment_count = fields.Integer(
        string='Number of attachments',
        required=False,
        readonly=False,
        index=False,
        default=0,
        store=False,
        help='Number of attachments',
        compute='_compute_ir_attachment_count'
    )

    @api.depends('ir_attachment_ids')
    def _compute_ir_attachment_count(self):
        for record in self:
            record.ir_attachment_count = len(record.ir_attachment_ids)

    answer_count = fields.Integer(
        string='Number of answers',
        required=False,
        readonly=False,
        index=False,
        default=0,
        help='Number of answers',
        store=False,
        compute='_compute_answer_count',
        search='_search_answer_count'
    )

    @api.depends('answer_ids')
    def _compute_answer_count(self):
        for record in self:
            record.answer_count = len(record.answer_ids)

    def _search_answer_count(self, operator, operand):
        supported = ['=', '!=', '<=', '<', '>', '>=']

        assert operator in supported, \
            UserError(_('Search operator not supported'))

        assert is_numeric(operand) or operand in [True, False], \
            UserError(_('Search value not supported'))

        operator, operand = fix_established(operator, operand)

        sql = ANSWER_COUNT_SEARCH.format(operator, operand)

        self.env.cr.execute(sql)
        ids = self.env.cr.fetchall()

        return [('id', 'in', ids)]

    category_count = fields.Integer(
        string='Number of categories',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of categories',
        store=False,
        compute='_compute_category_count'
    )

    @api.depends('category_ids')
    def _compute_category_count(self):
        for record in self:
            record.category_count = len(record.category_ids)

    version_count = fields.Integer(
        string='Number of versions',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of versions',
        store=False,
        compute='_compute_version_count'
    )

    @api.depends('version_ids')
    def _compute_version_count(self):
        for record in self:
            record.version_count = len(record.version_ids)

    is_uncategorized = fields.Boolean(
        string='Uncategorized',
        required=False,
        readonly=True,
        index=True,
        default=False,
        help=('Check if the question is related to a provisional topic, '
              'version or category'),
        compute='_compute_is_uncategorized',
        search='_search_is_uncategorized'
    )

    @api.depends('topic_id', 'version_ids', 'category_ids')
    def _compute_is_uncategorized(self):
        for record in self:
            provisional = record.mapped('topic_id.provisional')
            provisional.extend(record.mapped('version_ids.provisional'))
            provisional.extend(record.mapped('category_ids.provisional'))

            record.is_uncategorized = any(provisional)

    @api.model
    def _search_is_uncategorized(self, operator, value):
        assert operator in ['=', '!='] and value in [True, False], \
            _('Invalid search operation for closed field in attempt')

        self.env.cr.execute(SEARCH_IS_UNCATEGORIZED)
        result_set = self.env.cr.fetchall()

        if result_set:
            ids = [item[0] for item in result_set]

            if self._is_uncategorized_is_true(operator, value):
                domain = [('id', 'in', ids)]
            else:
                domain = [('id', 'not in', ids)]
        else:
            if self._is_uncategorized_is_true(operator, value):
                domain = FALSE_DOMAIN
            else:
                domain = TRUE_DOMAIN

        return domain

    @staticmethod
    def _is_uncategorized_is_true(operator, value):
        return operator == '=' and value or operator == '!=' and not value

    # --------------------------- EXPORT TO STRING ----------------------------

    markdown = fields.Text(
        string='Markdown',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Show question as markdown text',
        translate=False,
        compute='_compute_markdown',
        store=False
    )

    @api.depends(
        'name', 'preamble', 'answer_ids', 'ir_attachment_ids', 'description')
    def _compute_markdown(self):
        for record in self:
            record.markdown = record.to_string(True).strip()

    def _get_real_id(self, item=None):
        item = item or self

        item.ensure_one()

        if isinstance(item.id, models.NewId):
            return 0
        else:
            return item.id

    def to_string(self, editable=False):
        """ Export question contents as markdown text

        @param editable (bool): if it set to true IDs will be preserved,
        otherwise index or URLs will be used instead

        @return (str): returns a single text string it contains the
        contents of the all questions in the recordset
        """
        output = ''
        index = 0

        for record in self:
            lines = []
            index = record._get_real_id() if editable else index + 1

            # STEP 1: Append description line (one or more)
            desc_line = prepare_text(record.description or '', '>')
            if(desc_line):
                lines.append(desc_line)

            # STEP 2: Append each one of the attachment lines
            for attach in record.ir_attachment_ids:
                if editable:
                    src_value = self._get_real_id(attach)
                else:
                    src_value = getattr(attach, 'local_url')
                attach_line = '![{}]({})'.format(attach.name, src_value)
                lines.append(attach_line)

            # STEP 3: Append preamble line (one or more)
            pre_line = prepare_text(record.preamble or '')
            if(pre_line):
                lines.append(pre_line)

            # STEP 4: Append name line (unique)
            lines.append('{}. {}'.format(index, (record.name or '').strip()))

            # STEP 5: Append each one of the answers
            for aindex, answer in enumerate(record.answer_ids):
                letter = 'x' if answer.is_correct else chr(97 + aindex)
                lines.append('{}) {}'.format(
                    letter, (answer.name or '').strip()))

            # STEP 6: Append empty line (between questions)
            lines.append(linesep)

            # STEP 7: Store question lines in output buffer
            output += linesep.join(lines)

        return output

    # ---------------------------- EXPORT TO HTML -----------------------------

    html = fields.Html(
        string='Html',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Show question as HTML',
        compute='_compute_html',
        store=False
    )

    @api.depends(
        'name', 'preamble', 'answer_ids', 'ir_attachment_ids', 'description')
    def _compute_html(self):
        for record in self:
            record.html = record.to_html()

    def _get_values_for_template(self):
        answers = []
        images = []

        self.ensure_one()

        for answer_item in self.answer_ids:
            answers.append({
                'name': answer_item.name,
                'is_correct': answer_item.is_correct
            })

        for image_item in self.ir_attachment_image_ids:
            images.append({
                'id': self._get_real_id(image_item),
                'name': image_item.name
            })

        return {
            'index': self._get_real_id(),
            'name': self.name,
            'preamble': self.preamble,
            'answers': answers,
            'images': images
        }

    def to_html(self):
        output = ''

        template_xid = \
            'academy_tests.view_academy_tests_display_question_as_html'
        view_obj = self.env['ir.ui.view']

        for record in self:

            values = record._get_values_for_template()

            html = view_obj._render_template(template_xid, values)
            output += html  # .decode('utf8')

        return output

    # --------------- ONCHANGE EVENTS AND OTHER FIELD METHODS -----------------

    def _categorize_from_last_questions(self):
        """ Get the number of questions will be used to compute default
        topic, leve, etc.

        This value can be stored as ir.config.parameter

        Returns:
            int: number of questions will be used
        """

        key = 'academy_tests.categorize_from_last_questions'

        param_obj = self.env["ir.config_parameter"].sudo()
        value = param_obj.get_param(key, default='3')

        return self._safe_cast(value, int, 3)

    def default_type_id(self, type_id=None):
        """ Computes the type_id default value. This will be the most
        used in last writed questions.
        @param type_id (int): it allows external code to pass a default
        ID, this will be used when no alternative was found
        """
        uid = self._default_owner_id()
        num = self._categorize_from_last_questions()
        sql = FIND_MOST_USED_QUESTION_FIELD_VALUE_FOR_SQL.format(
            field='type_id', owner=uid, num=num)

        self.env.cr.execute(sql)
        data = self.env.cr.fetchone()

        return data[0] if data and data[0] else type_id

    def default_topic_id(self, topic_id=None):
        """ Computes the topic_id default value. This will be the most
        used in last writed questions.
        @param topic_id (int): it allows external code to pass a default
        ID, this will be used when no alternative was found
        """
        uid = self._default_owner_id()
        num = self._categorize_from_last_questions()
        sql = FIND_MOST_USED_QUESTION_FIELD_VALUE_FOR_SQL.format(
            field='topic_id', owner=uid, num=num)

        self.env.cr.execute(sql)
        data = self.env.cr.fetchone()

        return data[0] if data and data[0] else topic_id

    def default_version_ids(self):
        return self.topic_id.last_version()

    def default_level_id(self, level_id=None):
        """ Computes the level_id default value. This will be the most
        used in last writed questions or the intermediate level.
        @param level_id (int): it allows external code to pass a default
        ID, this will be used when no alternative was found
        """

        uid = self._default_owner_id()
        num = self._categorize_from_last_questions()
        sql = FIND_MOST_USED_QUESTION_FIELD_VALUE_FOR_SQL.format(
            field='level_id', owner=uid, num=num)

        self.env.cr.execute(sql)
        data = self.env.cr.fetchone()

        if data and data[0]:  # Try to compute most used level
            level_id = data[0]
        else:                 # Try to compute the intermediate level
            academy_level_domain = []
            academy_level_obj = self.env['academy.tests.level']
            academy_level_set = academy_level_obj.search(
                academy_level_domain, order="sequence ASC")

            if academy_level_set:
                middle = len(academy_level_set) // 2
                level_id = academy_level_set[middle].id

        return level_id

    def default_category_ids(self, force=False):
        """ Compute default (single) category from the current topic,
        this will be the most used in last questions of the current user
        or None.
        @param force (bool): if set to true then the first category will
        be used if no other suitable one is found.
        @note: **IMPORTANT**, this method is not used to compute the
        default value, this only allows external code to invoke it.
        """
        uid = self._default_owner_id()
        result = [(5, 0, 0)]    # Unlink all

        if self.topic_id and self.topic_id.category_ids:
            sql = FIND_MOST_USED_QUESTION_CATEGORY_VALUE_SQL.format(
                topic=self.topic_id.id, owner=uid)
            self.env.cr.execute(sql)
            data = self.env.cr.fetchone()
            if data and data[0]:
                result = [(6, 0, [data[0]])]
            elif force:
                default_id = self.topic_id.category_ids[0].id
                result = [(6, 0, [default_id])]

        return result

    @api.onchange('description')
    def _onchange_description(self):
        self.markdown = self.to_string(True).strip()

    @api.onchange('preamble')
    def _onchange_preamble(self):
        self.markdown = self.to_string(True).strip()
        self.html = self.to_html()

    @api.onchange('name')
    def _onchange_name(self):
        self.markdown = self.to_string(True).strip()
        self.html = self.to_html()

    @api.onchange('answer_ids')
    def _onchange_answer_ids(self):
        self.markdown = self.to_string(True).strip()
        self.html = self.to_html()

    @api.onchange('topic_id')
    def _onchange_academy_topid_id(self):
        """ Updates domain form category_ids, this shoud allow categories
        only in the selected topic.
        """
        self.category_ids = False
        self.version_ids = self.default_version_ids()

    @api.onchange('ir_attachment_ids')
    def _onchange_ir_attachment_id(self):
        self._compute_ir_attachment_image_ids()
        self.markdown = self.to_string(True).strip()
        self.html = self.to_html()

    # ---------------------------- CONSTRAINTS  -------------------------------

    _sql_constraints = [
        (
            'exclude_it_self_in_depends_on_id',
            'CHECK(depends_on_id <> id)',
            _('A question cannot depend on itself')
        )
    ]

    @api.constrains('version_ids')
    def _check_version_ids(self):
        msg = _('Topic {} must have at least one version')
        for record in self:
            if not record.version_ids:
                raise ValidationError(msg.format(record.name))

    @api.constrains('category_ids')
    def _check_category_ids(self):
        msg = _('Topic {} must have at least one category')
        for record in self:
            if not record.category_ids:
                raise ValidationError(msg.format(record.name))

    @api.constrains('name', 'preamble', 'topic_id', 'answer_ids',
                    'ir_attachment_ids', 'version_ids', 'status')
    def _check_question_is_unique(self):
        msg = _('There is already a question «Q#{}» with this wording')

        for record in self:

            if record.status != 'ready':
                continue

            similar_set = record._search_similars()
            thisans = record._join_answers()
            thisattach = record._join_attachments()

            for similar in similar_set:
                simans = similar._join_answers()
                if thisans and simans and thisans == simans:
                    raise ValidationError(msg.format(similar.id))

                simattach = similar._join_attachments()
                if thisattach and simattach and thisattach == simattach:
                    raise ValidationError(msg.format(similar.id))

    def _search_similars(self):
        """ Used in _check_question_is_unique
        """

        self.ensure_one()

        domain = [
            ('id', '!=', self.id),
            ('status', '=', 'ready'),
            ('topic_id', '=', self.topic_id.id),
            ('name', 'ilike', self.name),
            ('preamble', 'ilike', self.preamble),
        ]

        return self.search(domain)

    def _join_answers(self):
        """ Used in _check_question_is_unique
        """

        answers = []

        self.ensure_one()

        for answer in self.answer_ids:
            prefix = 'x' if answer.is_correct else '#'
            name = answer.name.lower()
            answers.append('{}{}'.format(prefix, name))

        answers.sort()

        return ';'.join(answers)

    def _join_attachments(self):
        """ Used in _check_question_is_unique
        """

        self.ensure_one()
        checksums = self.mapped('ir_attachment_ids.checksum')

        checksums.sort()

        return ';'.join(checksums)

    @api.constrains('answer_ids', 'name')
    def _check_answer_ids(self):
        """ Check if question have at last one valid answer
        """
        if self.active:
            if True not in self.answer_ids.mapped('is_correct'):
                message = _(u'You must specify at least one correct answer')
                raise ValidationError(message)
            if False not in self.answer_ids.mapped('is_correct'):
                message = _(u'You must specify at least one incorrect answer')
                raise ValidationError(message)

    @api.constrains('depends_on_id')
    def _cyclic_redundancy_check(self):
        msg = 'Cyclic redundancy error when setting question dependencies.'
        for record in self:
            dependent_ids = record.dependent_ids.mapped('id')
            if record.depends_on_id.id in dependent_ids:
                raise ValidationError(msg)

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

    def _update_ir_attachments(self):
        """ Apparently Odoo links the attachment to the record from which it is
        saved, but this block it from being used from other questions.

        This method unlinks the attachment from the specific question.
        """

        attachment_set = self.mapped('ir_attachment_ids')
        values = {'res_model': None, 'res_id': 0, 'public': True}

        attachment_set.sudo().write(values)

    def name_get(self):
        ''' Compute display_name field value.
        '''

        pattern = '{}. {}'
        result = []

        for record in self:
            if isinstance(record.id, models.NewId):
                text = _('New question')
            else:
                text = pattern.format(record.id, record.name)

            result.append((record.id, text))

        return result

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        """ There can be no duplicates in production, so all copies must be
        created with draft status.

        Args:
            default (None, optional): values to overwrite in the copy

        Returns:
            object: a copy of this record with ``draft`` as status value
        """
        parent = super(AcademyTestsQuestion, self)

        default = dict(default or {})
        default['status'] = 'draft'

        return parent.copy(default=default)

    @api.model
    def create(self, values):
        """ Update attachment records
        """

        _super = super(AcademyTestsQuestion, self)
        result = _super.create(values)

        result._update_ir_attachments()

        return result

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

        self._update_ir_attachments()

        return result

    # --------------------------- IMPORT FROM TEXT ----------------------------

    @staticmethod
    def _safe_cast(val, to_type, default=None):
        """ Performs a safe cast between `val` type to `to_type`

        @param val: value will be converted
        @param to_type: type of value to return
        @param default: value will be returned if conversion fails

        @return result of conversion or given default
        """

        try:
            return to_type(val)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _equal(str1, str2):
        """ Compare two given strings ignoring case

        @param str1 (str): first string to compare
        @param str2 (str): first string to compare

        @return True if both strings are equal or false otherwise
        """

        str1 = (str1 or '').lower()
        str2 = (str2 or '').lower()

        return str1 == str2

    @staticmethod
    def _split_in_line_groups(content):
        """ Splits content into lines and then splits these lines into
        groups using empty lines as a delimiter.

        @param content (str): markdown text will be converted in one or
        more questions

        @return (list) lines grouped by question
        """

        content = content.strip('\r\n\t ')

        lines = content.splitlines(False)
        groups = []

        group = []
        numlines = len(lines)
        for index in range(0, numlines):
            if lines[index] == '':
                groups.append(group)
                group = []
            elif index == (numlines - 1):
                group.append(lines[index])
                groups.append(group)
            else:
                group.append(lines[index])

        return groups

    @staticmethod
    def _assert_mandatory(values):
        """ Perform serveral asserts about given `values` dictionary
        which must be true

        @param values (dict): dictionary of values will be used as base
        to create new questions
        """

        assert 'topic_id' in values.keys(), \
            _('Topic is mandatory for questions')

        assert 'category_ids' in values.keys(), \
            _('Category is mandatory for questions')

        assert 'type_id' in values.keys(), \
            _('Type is mandatory for questions')

    @api.model
    def _ensure_base_values(self, values):
        """ Make sure mandatory values exist in given dictionary, if any
        of them are missing it will be added with its default value

        @param values (dict): dictionary of values will be used as base
        to create new questions
        """

        if 'level_id' not in values:
            values['level_id'] = self.default_level_id()

        if 'answer_ids' not in values:
            values['answer_ids'] = []

        if 'ir_attachment_ids' not in values:
            values['ir_attachment_ids'] = []

        if 'description' not in values:
            values['description'] = ''

        if 'preamble' not in values:
            values['preamble'] = ''

    @staticmethod
    def _build_single_regular_expresion():
        """ Build the regular expression will be used to search for
        parts of the question in a given text string.

        @return (str) return regular expresion
        """

        nom = r'(^[0-9]+\. )'
        ans = r'(((^[a-wy-z])|(^x))\) )'
        dsc = r'(^> )'
        att = r'(^\!\[([^]]+)\]\(([^)]+))'

        return r'({}|{}|{}|{})?(.+)'.format(nom, ans, dsc, att)

    @staticmethod
    def _append_line(_in_buffer, line):
        """ Appends new line using previous line break when buffer is not empty
        """

        if _in_buffer:
            _in_buffer = _in_buffer + linesep + line
        else:
            _in_buffer = line

        return _in_buffer

    def _process_attachment_groups(self, groups):
        """
        """

        uri = groups[Mi.URI.value]
        title = groups[Mi.TITLE.value]
        record = self.env['ir.attachment']

        # STEP 1: Try to find attachment by `id` field
        numericURI = self._safe_cast(uri, int, 0)
        if not numericURI:
            match = search(r'\/([0-9]+)\?', uri)
            if match:
                numericURI = self._safe_cast(match.group(1), int, 0)

        if numericURI:
            record = record.browse(numericURI)

        # STEP 3: Raise error if number of found items is not equal to one
        if not record:
            message = _('Invalid attachment URI: ![%s](%s)')
            raise ValidationError(message % (title, uri))
        elif len(record) > 1:
            message = _('Duplicate attachment URI: %s')
            raise ValidationError(message % (title, uri))

        # STEP 4: Return ID
        return record.id

    def _process_line_group(self, line_group, values):
        """ Gets description, image, preamble, statement, and answers
        from a given group of lines
        """

        self._assert_mandatory(values)
        self._ensure_base_values(values)

        sequence = 0

        regex = self._build_single_regular_expresion()
        flags = UNICODE | IGNORECASE

        for line in line_group:
            found = search(regex, line, flags)
            if found:
                groups = found.groups()

                if groups[Mi.QUESTION.value]:
                    values['name'] = groups[Mi.CONTENT.value]

                elif groups[Mi.ANSWER.value]:
                    sequence = sequence + 1
                    ansvalues = {
                        'name': groups[Mi.CONTENT.value],
                        'is_correct': (groups[Mi.TRUE.value] is not None),
                        'sequence': sequence
                    }
                    values['answer_ids'].append((0, None, ansvalues))

                elif groups[Mi.DESCRIPTION.value]:
                    values['description'] = self._append_line(
                        values['description'], groups[Mi.CONTENT.value])

                elif groups[Mi.IMAGE.value]:
                    ID = self._process_attachment_groups(groups)
                    if ID:
                        values['ir_attachment_ids'].append((4, ID, None))

                else:
                    values['preamble'] = self._append_line(
                        values['preamble'], groups[Mi.CONTENT.value])

        return values

    def _build_value_set(self, groups, base):
        """ Transform a given list of groups of lines in a valid set of
        values to use it in the question create method.

        @param groups (list): list of lists of lines
        """

        value_set = []
        for group in groups:
            values = self._process_line_group(group, base)
            value_set.append(values)

        return value_set

    @api.model
    def from_string(self, content, defaults={}, edit=False):
        groups = self._split_in_line_groups(content)

        base = {
            'topic_id': defaults.get('topic_id', 1),
            'category_ids': defaults.get('category_ids', 1),
            'type_id': defaults.get('type_id', 1)
        }

        return self._build_value_set(groups, base)

    @api.model
    def read_as_string(self, res_id, editable=False):
        item = self.env[self._name].browse(res_id)

        return item.to_string(editable) if item else ''

    # ---------------------------- BUTTON ACTIONS -----------------------------

    def switch_status(self):
        for record in self:
            if record.status == 'draft':
                record.status = 'ready'
            else:
                record.status = 'draft'

    def open_form_view(self, res_id=None):

        view = self.env.ref('academy_tests.view_academy_question_form')

        context = self.env.context or {}
        res_id = self[0].id if self else None

        if not res_id:
            res_id = self.env.context.get('active_id', False)
            assert res_id and context.get('active_model') == self._name, \
                _('The question has not been specified')

        return {
            'name': _('Question'),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': self._name,
            'view_id': view.id,
            'res_id': res_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': '[]',
            'context': self.env.context,
            'flags': {'mode': 'readonly'}
        }
