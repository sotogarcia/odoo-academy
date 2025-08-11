# -*- coding: utf-8 -*-
""" AcademyTestsQuestion

This module contains the academy.tests.question Odoo model which stores
all academy tests question attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError, UserError
from odoo.osv.expression import FALSE_DOMAIN

from logging import getLogger
from os import linesep
from re import search, UNICODE, IGNORECASE
from enum import Enum

import lxml.etree as ET
import mimetypes
from io import BytesIO

from .utils.libuseful import prepare_text, fix_established, is_numeric

from .utils.sql_operations import ACADEMY_QUESTION_ENSURE_CHECKSUMS
from .utils.sql_operations import FIND_MOST_USED_QUESTION_FIELD_VALUE_FOR_SQL
from .utils.sql_operations import FIND_MOST_USED_QUESTION_CATEGORY_VALUE_SQL

from .utils.sql_inverse_searches import ANSWER_COUNT_SEARCH
from .utils.sql_inverse_searches import UNCATEGORIZED_QUESTION_SEARCH

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
        'mail.thread'
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
        track_visibility='onchange'
    )

    preamble = fields.Text(
        string='Preamble',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='What it is said before beginning to question',
        translate=True,
        track_visibility='onchange'
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
              'hide record without removing it'),
        track_visibility='onchange'
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
        track_visibility='onchange',
    )

    topic_version_ids = fields.Many2many(
        string='Topic versions',
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self.default_topic_version_ids(),
        help='Choose which versions of the topic this question belongs to',
        comodel_name='academy.tests.topic.version',
        relation='academy_tests_question_topic_version_rel',
        column1='question_id',
        column2='topic_version_id',
        domain=[],
        context={},
        limit=None,
        track_visibility='onchange'
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
        track_visibility='onchange',
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
        track_visibility='onchange',
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
        auto_join=False,
        track_visibility='onchange'
    )

    test_ids = fields.One2many(
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

    impugnment_ids = fields.One2many(
        string='Impugnments',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='List current impugnments to this question',
        comodel_name='academy.tests.question.impugnment',
        inverse_name='question_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    checksum = fields.Char(
        string='Checksum',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Question checksum',
        size=32,
        translate=False
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
        track_visibility='onchange'
    )

    authorship = fields.Boolean(
        string='Authorship',
        required=False,
        readonly=False,
        index=True,
        default=True,
        help='Check it to indicate that it is your own authorship',
        track_visibility='onchange'
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
        copy=False
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
        copy=False
    )

    duplicated_ids = fields.Many2manyView(
        string='Duplicates',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help=False,
        comodel_name='academy.tests.question',
        relation='academy_tests_question_duplicated_rel',
        column1='question_id',
        column2='duplicate_id',
        domain=[],
        context={},
        limit=None,
        copy=False
    )

    # This field can have a maximum of one record. It's used in some domains
    # to check if question is not the original.
    original_ids = fields.Many2manyView(
        string='Original',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help=False,
        comodel_name='academy.tests.question',
        relation='academy_tests_question_duplicated_rel',
        column1='duplicate_id',
        column2='question_id',
        domain=[],
        context={},
        limit=None,
        copy=False
    )

    color = fields.Integer(
        string='Color Index',
        required=True,
        readonly=True,
        index=False,
        default=10,
        help='Display color based on dependency and status',
        store=False,
        compute=lambda self: self._compute_color()
    )

    changelog_entry_ids = fields.One2many(
        string='Changelog entries',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help=False,
        comodel_name='academy.tests.question.changelog.entry',
        inverse_name='question_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    topic_module_link_ids = fields.Many2manyView(
        string='Links module-topic',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='List all module-topic links this question is related to',
        comodel_name='academy.tests.topic.training.module.link',
        relation='academy_tests_topic_training_module_link_question_rel',
        column1='question_id',
        column2='topic_module_link_id',
        domain=[],
        context={},
        limit=None,
        copy=False
    )

    def _compute_color(self):
        for record in self:
            if record.status == 'draft':
                record.color = 1
            elif record.depends_on_id:
                record.color = 3
            else:
                record.color = 10

    # -------------------------- SQL CONSTRANINTS  ----------------------------

    _sql_constraints = [
        (
            'exclude_it_self_in_depends_on_id',
            'CHECK(depends_on_id <> id)',
            _('A question cannot depend on itself')
        )
    ]

    # -------------------------- MANAGEMENT FIELDS ----------------------------

    dependency_count = fields.Integer(
        string='Dependencies',
        required=False,
        readonly=False,
        index=False,
        default=0,
        help='Number of attachments',
        store=False,
        compute=lambda self: self._compute_dependency_count()
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
        compute=lambda self: self._compute_dependent_count()
    )

    @api.depends('dependent_ids')
    def _compute_dependent_count(self):
        for record in self:
            record.dependent_count = len(record.dependent_ids)

    impugnment_count = fields.Integer(
        string='Impugnment count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        store=False,
        help='Show the number of current impugnments to this question',
        compute=lambda self: self._compute_impugnment_count()
    )

    @api.depends('impugnment_ids')
    def _compute_impugnment_count(self):
        for record in self:
            record.impugnment_count = len(record.impugnment_ids)

    duplicated_count = fields.Integer(
        string='Duplicated count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show the number of duplicate questions',
        compute=lambda self: self._compute_duplicated_count()
    )

    @api.depends('duplicated_ids')
    def _compute_duplicated_count(self):
        for record in self:
            record.duplicated_count = len(record.duplicated_ids)

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

    attachment_count = fields.Integer(
        string='Number of attachments',
        required=False,
        readonly=False,
        index=False,
        default=0,
        store=False,
        help='Number of attachments',
        compute=lambda self: self._compute_attachment_count()
    )

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
        store=False,
        compute=lambda self: self._compute_answer_count(),
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
        compute=lambda self: self._compute_category_count()
    )

    @api.depends('category_ids')
    def _compute_category_count(self):
        for record in self:
            record.category_count = len(record.category_ids)

    uncategorized = fields.Boolean(
        string='Uncategorized',
        required=False,
        readonly=True,
        index=False,
        default=False,
        help='Show if question has been categorized',
        store=False,
        compute='_compute_uncategorized',
        search='_search_uncategorized',
    )

    @api.depends('topic_id', 'topic_version_ids', 'category_ids')
    def _compute_uncategorized(self):
        for record in self:
            topic_id = record.topic_id
            is_valid_topic = topic_id.active and topic_id.provisional is False

            category_ids = record.category_ids
            act_cats = all(category_ids.mapped('active'))
            end_cats = not any(category_ids.mapped('provisional'))

            version_ids = record.topic_version_ids
            act_vers = all(version_ids.mapped('active'))
            end_vers = not any(version_ids.mapped('provisional'))

            record.uncategorized = (topic_id and is_valid_topic) and \
                (category_ids and act_cats and end_cats) and \
                (version_ids and act_vers and end_vers)

    def _search_uncategorized(self, operator, value):
        self.env.cr.execute(UNCATEGORIZED_QUESTION_SEARCH)
        ids = self.env.cr.fetchall()

        return [('id', operator, ids)]

    # --------------- ONCHANGE EVENTS AND OTHER FIELD METHODS -----------------

    def default_type_id(self, type_id=None):
        """ Computes the type_id default value. This will be the most
        used in last writed questions.
        @param type_id (int): it allows external code to pass a default
        ID, this will be used when no alternative was found
        """
        uid = self.default_owner_id()
        sql = FIND_MOST_USED_QUESTION_FIELD_VALUE_FOR_SQL.format(
            field='type_id', owner=uid)

        self.env.cr.execute(sql)
        data = self.env.cr.fetchone()

        return data[0] if data and data[0] else type_id

    def default_topic_id(self, topic_id=None):
        """ Computes the topic_id default value. This will be the most
        used in last writed questions.
        @param topic_id (int): it allows external code to pass a default
        ID, this will be used when no alternative was found
        """
        uid = self.default_owner_id()
        sql = FIND_MOST_USED_QUESTION_FIELD_VALUE_FOR_SQL.format(
            field='topic_id', owner=uid)

        self.env.cr.execute(sql)
        data = self.env.cr.fetchone()

        return data[0] if data and data[0] else topic_id

    def default_topic_version_ids(self):
        return self.topic_id.last_version()

    def default_level_id(self, level_id=None):
        """ Computes the level_id default value. This will be the most
        used in last writed questions or the intermediate level.
        @param level_id (int): it allows external code to pass a default
        ID, this will be used when no alternative was found
        """

        uid = self.default_owner_id()
        sql = FIND_MOST_USED_QUESTION_FIELD_VALUE_FOR_SQL.format(
            field='level_id', owner=uid)

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
        uid = self.default_owner_id()
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

    # @api.onchange('description')
    # def _onchange_description(self):
    #     self.markdown = self.to_string(True).strip()

    # @api.onchange('preamble')
    # def _onchange_preamble(self):
    #     self.markdown = self.to_string(True).strip()
    #     self.html = self.to_html()

    # @api.onchange('name')
    # def _onchange_name(self):
    #     self.markdown = self.to_string(True).strip()
    #     self.html = self.to_html()

    # @api.onchange('answer_ids')
    # def _onchange_answer_ids(self):
    #     self.markdown = self.to_string(True).strip()
    #     self.html = self.to_html()

    @api.onchange('topic_id')
    def _onchange_academy_topid_id(self):
        """ Updates domain form category_ids, this shoud allow categories
        only in the selected topic.
        """
        self.category_ids = False
        self.topic_version_ids = self.default_topic_version_ids()

    @api.onchange('ir_attachment_ids')
    def _onchange_ir_attachment_id(self):
        self._compute_ir_attachment_image_ids()
        # self.markdown = self.to_string(True).strip()
        # self.html = self.to_html()

    # -------------------------- PYTHON CONSTRAINS ----------------------------

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
    def _check_no_circular_dependency(self):
        message = _('Circular dependency detected in question "%s".')

        for record in self:
            current = record.depends_on_id
            while current:
                if current == record:
                    raise ValidationError(message % record.name)
                current = current.depends_on_id

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

        if self._has_tracked_fields(values):
            self._notify_related_tests()

        return result

    # ----------------------- MESSAGING METHODS ------------------------

    def _track_subtype(self, init_values):
        self.ensure_one()

        if('active' not in init_values):
            if 'owner_id' in init_values:
                xid = 'academy_tests.academy_tests_question_owned'
            else:
                xid = 'academy_tests.academy_tests_question_written'

            return self.env.ref(xid)
        else:
            _super = super(AcademyTestsQuestion, self)
            return _super._track_subtype(init_values)

    # -------------------------- AUXILIARY METHODS ----------------------------

    @staticmethod
    def safe_cast(val, to_type, default=None):
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
        numericURI = self.safe_cast(uri, int, 0)
        if not numericURI:
            match = search(r'\/([0-9]+)\?', uri)
            if match:
                numericURI = self.safe_cast(match.group(1), int, 0)

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

    # ---------------------------- PUBLIC METHODS -----------------------------

    markdown = fields.Text(
        string='Markdown',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Show question as markdown text',
        translate=False,
        compute=lambda self: self.compute_markdown(),
        store=False
    )

    @api.depends(
        'name', 'preamble', 'answer_ids', 'attachment_ids', 'description')
    def compute_markdown(self):
        for record in self:
            record.markdown = record.to_string(True).strip()

    html = fields.Html(
        string='Html',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Show question as HTML',
        compute=lambda self: self.compute_html(),
        store=False
    )

    @api.depends(
        'name', 'preamble', 'answer_ids', 'attachment_ids', 'description')
    def compute_html(self):
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

    def _get_real_id(self, item=None):
        item = item or self

        item.ensure_one()

        if isinstance(item.id, models.NewId):
            return item._origin.id
        else:
            return item.id

    def to_html(self):
        output = ''

        template_xid = \
            'academy_tests.view_academy_tests_display_question_as_html'
        view_obj = self.env['ir.ui.view']

        for record in self:

            values = record._get_values_for_template()

            html = view_obj.render_template(template_xid, values)
            output += html.decode('utf8')

        return output

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
            index = self._get_real_id(record) if editable else index + 1

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

    def switch_status(self):
        for record in self:
            if record.status == 'draft':
                record.status = 'ready'
            else:
                record.status = 'draft'

    @api.model
    def ensure_checksums(self):
        """ This method uses an SQL query to UPDATE the checksum in all the
        question records when this field has a null value.
        """
        sql = ACADEMY_QUESTION_ENSURE_CHECKSUMS

        self.env.cr.execute(sql)
        self.env.cr.commit()

    def impugn(self):
        self.ensure_one()

        act_xid = 'academy_tests.action_question_impugnment_act_window'
        act_item = self.env.ref(act_xid)

        act_dict = dict(
            name=act_item.name,
            view_mode='form',
            view_id=False,
            view_type='form',
            res_model='academy.tests.question.impugnment',
            type='ir.actions.act_window',
            nodestroy=True,
            target='new',
            context={
                'default_question_id': self.id,
                'default_owner_id': self.owner_id.id if self.owner_id else 1
            }
        )

        return act_dict

    def update_questions_dialog(self):
        wizard_model = 'academy.tests.update.questions.wizard'
        
        wizard_set = self.env[wizard_model]
        wizard_set = wizard_set.create({})
        wizard_set.set_questions(self)

        return {
            'name': _('Update questions'),
            'type': 'ir.actions.act_window',
            'res_model': wizard_model,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'domain': [],
            'res_id': wizard_set.id
        }

    def show_impugnments(self):
        self.ensure_one()

        act_xid = 'academy_tests.action_question_impugnment_act_window'
        act_item = self.env.ref(act_xid)

        act_dict = dict(
            name=act_item.name,
            view_mode='tree,form,graph',
            view_id=False,
            view_type='form',
            res_model='academy.tests.question.impugnment',
            type='ir.actions.act_window',
            target='current',
            context={
                'default_question_id': self.id,
                'default_owner_id': self.owner_id.id if self.owner_id else 1
            },
            domain=[('question_id', '=', self.id)]
        )

        return act_dict

    def show_duplicates(self):
        self.ensure_one()

        act_xid = ('academy_tests.'
                   'action_remove_duplicate_questions_wizard_act_window')
        act_item = self.env.ref(act_xid)

        act_dict = dict(
            name=act_item.name,
            view_mode='form',
            view_id=False,
            view_type='form',
            res_model=act_item.res_model,
            type='ir.actions.act_window',
            target='new',
            context={
                'default_question_id': self.id
            }
        )

        return act_dict

    @api.model
    def domain_to_sql(self, domain):
        items = self._where_calc(domain).get_sql()

        return items[1] % tuple(items[2]) if items else 'TRUE'

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
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': self.env.context,
            'flags': {'mode': 'readonly'}
        }

    def to_moodle(self, encoding='utf8', prettify=True, xml_declaration=True,
                  category=None, correction_scale=None):
        quiz = self._moodle_create_quiz(category=category)

        for record in self:
            node = record._to_moodle(correction_scale=correction_scale)
            quiz.append(node)

        file = BytesIO()
        root = quiz.getroottree()
        root.write(file, encoding=encoding, pretty_print=prettify,
                   xml_declaration=xml_declaration)

        return file.getvalue()

    @staticmethod
    def _moodle_create_quiz(category=None):
        category = category or _('Odoo export')

        node = ET.Element('quiz')

        qnode = ET.SubElement(node, 'question', type='category')
        cnode = ET.SubElement(qnode, 'category')
        ET.SubElement(cnode, 'text').text = '$course$/top'

        qnode = ET.SubElement(node, 'question', type='category')
        cnode = ET.SubElement(qnode, 'category')
        ET.SubElement(cnode, 'text').text = '$course$/top/{}'.format(category)

        return node

    def _answer_count(self):
        self.ensure_one()

        right_set = self.answer_ids.filtered(lambda a: a.is_correct)

        return len(self.answer_ids), len(right_set)

    @staticmethod
    def _moodle_cdata(text=None):
        return ET.CDATA(text) if text else ''

    @staticmethod
    def _moodle_paragraphs(text, prettify=True):
        paragraphs = []
        lines = text.splitlines()
        sep = '\n' if prettify else ''

        for line in lines:
            paragraphs.append('<p>{}</p>'.format(line))

        return sep.join(paragraphs)

    @staticmethod
    def _moodle_create_node(multichoice=False):
        node = ET.Element('question', type='multichoice')

        ET.SubElement(node, 'hidden').text = '0'
        ET.SubElement(node, 'shuffleanswers').text = 'false'
        ET.SubElement(node, 'answernumbering').text = 'abc'
        ET.SubElement(node, 'single').text = 'false' if multichoice else 'true'

        return node

    def _moodle_append_name(self, node, name=None):
        if not name:
            name = '{}-{}'.format('ID', self.id)

        sub = ET.SubElement(node, 'name')
        ET.SubElement(sub, 'text').text = name

    def _moodle_append_description(self, node, prettify=True):
        description = self._moodle_paragraphs(self.description or '', prettify)
        sub = ET.SubElement(
            node, 'generalfeedback', format='moodle_auto_format')
        ET.SubElement(sub, 'text').text = self._moodle_cdata(description)

    def _moodle_append_statement(self, node, prettify=True):
        tag = '<img src="@@PLUGINFILE@@/{fn}" alt="{fn}" role="presentation">'
        html = ''

        snode = ET.SubElement(node, 'questiontext', format='html')

        if self.ir_attachment_ids:
            pattern = '<div style="display: flex;">{}</div>{}'
            sep = '\n' if prettify else ''
            img_tags = []

            for attach in self.ir_attachment_ids:
                ext = mimetypes.guess_extension(attach.mimetype)
                fname = '{}{}'.format(attach.name, ext)

                attnode = ET.SubElement(
                    snode, 'file', name=fname, path="/", encoding="base64")
                attnode.text = attach.datas

                img_tags.append(tag.format(fn=fname))

            html += pattern.format(sep.join(img_tags), sep)

        if self.preamble:
            html += self._moodle_paragraphs(self.preamble or '', prettify)

        html += self._moodle_paragraphs(self.name or '', prettify)

        ET.SubElement(snode, 'text').text = self._moodle_cdata(html)

    def _moodle_append_answer(self, node, answer, fraction):
        ans_node = ET.SubElement(
            node, 'answer', format='moodle_auto_format', fraction=fraction)
        ET.SubElement(ans_node, 'text').text = self._moodle_cdata(answer.name)

        desc_node = ET.SubElement(
            ans_node, 'feedback', format='moodle_auto_format')
        ET.SubElement(desc_node, 'text').text = \
            self._moodle_cdata(answer.description or '')

    @staticmethod
    def _round_to_moodle(value):
        valid = [
            0, 5, 10, 11.11111, 12.5, 14.28571, 16.66667, 20, 25, 30,
            33.33333, 40, 50, 60, 66.66667, 70, 75, 80, 83.33333, 90, 100
        ]

        abs_value = abs(value)
        closest = min(valid, key=lambda x: abs(x - abs_value))

        return closest if value >= 0 else -closest

    def _to_moodle(self, name=None, correction_scale=None):
        self.ensure_one()

        a_total, a_right = self._answer_count()

        if not correction_scale:
            scale_xid = 'academy_tests.academy_tests_correction_scale_default'
            correction_scale = self.env.ref(scale_xid)

        wrong = float(correction_scale.wrong)
        right = float(correction_scale.right)

        good = 100.0
        bad = round((wrong / right) * 100.0, 5)

        good = self._round_to_moodle(good)
        bad = self._round_to_moodle(bad)

        node = self._moodle_create_node(multichoice=(a_right > 1))

        self._moodle_append_name(node, name)
        self._moodle_append_statement(node)
        self._moodle_append_description(node)

        for answer in self.answer_ids:
            fraction = str(good) if answer.is_correct else str(bad)
            self._moodle_append_answer(node, answer, fraction)

        return node

    def download_as_moodle_xml(self):
        question_ids = self.mapped('id')

        if not question_ids:
            raise(_('There are no questions'))

        ids_str = ','.join([str(item) for item in question_ids])

        relative_url = '/academy_tests/moodle/questions?question_ids={}'
        return {
            'type': 'ir.actions.act_url',
            'url': relative_url.format(ids_str),
            'target': 'self',
        }

    def _notify_related_tests(self):
        """
        Notify related tests that changes have been made to linked questions.

        This method posts a message to the related academy.tests.test
        recordset, indicating whether a single question or multiple questions
        were updated.
        """

        related_tests = self.mapped('test_ids.test_id')
        if not related_tests:
            return self.env['academy.tests.test']  # Empty recordset

        subject = _('Question update notification')

        if len(self) == 1:
            message = _('Changes have been made to the question with ID {}.')
            message = message.format(self.id)
        else:
            message = _('Changes have been made to several linked questions.')

        for test in related_tests:
            test.message_post(
                body=message, subject=subject, message_type='notification')

        return related_tests

    @api.model
    def _has_tracked_fields(self, values):
        """
        Check if any of the updated fields have track_visibility set to
        something other than 'none'.

        Args:
            values (dict): The fields and values to be updated.

        Returns:
            bool: True if any field has track_visibility != 'none', False
            otherwise.
        """
        for field_name in values.keys():
            if field_name == 'answer_ids':
                return True

            field = self._fields.get(field_name)
            if field and getattr(field, 'track_visibility', 'none') != 'none':
                return True

        return False
