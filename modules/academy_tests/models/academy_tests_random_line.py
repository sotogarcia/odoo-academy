# -*- coding: utf-8 -*-
""" Academy Tests Random Wizard Line

This module contains the academy.tests.random.line. an unique Odoo model
which contains all Academy Tests Random Wizard Line  attributes and behavior.
"""


from logging import getLogger
from datetime import datetime
from odoo.osv.expression import AND, FALSE_DOMAIN, TRUE_DOMAIN
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _


_logger = getLogger(__name__)


WIZARD_LINE_STATES = [
    ('step1', _('General')),
    ('step2', _('Categorization')),
    ('step3', _('Tests')),
    ('step4', _('Questions')),
    ('step5', _('Special'))
]

CHECK_ANSWER_VALUES = ('CHECK(minimum_answers > 1 AND maximum_answers > 1 AND '
                       'minimum_answers <= maximum_answers)')


# pylint: disable=locally-disabled, R0903, W0212
class AcademyTestsRandomTemplateLine(models.Model):
    """ This model is the representation of the academy tests random line
    """

    _name = 'academy.tests.random.line'
    _description = u'Academy tests, random line'

    _rec_name = 'name'
    _order = 'sequence ASC, id ASC'

    _debug = True

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
        auto_join=True
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

    owner_ids = fields.Many2many(
        string='Owners',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Limit questions to those owned by certain users',
        comodel_name='res.users',
        relation='academy_tests_random_wizard_line_res_users_rel',
        column1='wizard_line_id',
        column2='user_id',
        domain=[],
        context={},
        limit=None
    )

    exclude_owners = fields.Boolean(
        string='Exclude selected owners',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it this to disallow selected records instead allow them'
    )

    authorship = fields.Selection(
        string='Authorship',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Limit questions to those created by their owner',
        selection=[
            ('own', 'Own'),
            ('third', 'Third-party')
        ]
    )

    attachments = fields.Selection(
        string='Attachments',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Limit questions to those have attachments',
        selection=[
            ('with', 'With attachments'),
            ('without', 'Without attachments')
        ]
    )

    categorization_ids = fields.One2many(
        string='Categorization',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Add or remove topics, versiones and categories',
        comodel_name='academy.tests.random.line.categorization',
        inverse_name='random_line_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None,
        copy=True
    )

    exclude_categorization = fields.Boolean(
        string='Exclude categorization lines',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to disallow selected records instead allow them'
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

    test_ids = fields.Many2many(
        string='Random line tests',
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

    tests_by_context = fields.Boolean(
        string='Tests by context',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Get the criteria from the context has been given in the wizard'
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

    questions_by_context = fields.Boolean(
        string='Questions by context',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Get the criteria from the context has been given in the wizard'
    )

    minimum_answers = fields.Integer(
        string='Minimum',
        required=True,
        readonly=False,
        index=False,
        default=4,
        help='Choose minimum number of answers'
    )

    maximum_answers = fields.Integer(
        string='Maximum',
        required=True,
        readonly=False,
        index=False,
        default=4,
        help='Choose maximum number of answers'
    )

    number_of_answers = fields.Boolean(
        string='Number of answers',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Limit to questions with a number of answers between'
    )

    exclude_answers = fields.Boolean(
        string='Out of limits',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help=('Check it this to choose questions with number of answers not '
              'between given minimum and maximum values')
    )

    test_block_id = fields.Many2one(
        string='Test block',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.test.block',
        domain=[],
        context={},
        ondelete='set null',
        auto_join=False
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

    categorization_count = fields.Integer(
        string='Categorization records',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of categorization records',
        store=False,
        compute='compute_categorization_count'
    )

    @api.depends('categorization_ids')
    def compute_categorization_count(self):
        """ This computes topic_count field """
        for record in self:
            record.categorization_count = len(record.categorization_ids)

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

    training_ref = fields.Reference(
        string='Training',
        help='Choose training item to which the test will be assigned',
        related='random_template_id.training_ref'
    )

    training_type = fields.Selection(
        string='Training type',
        related='random_template_id.training_type'

    )

    _sql_constraints = [
        (
            'CHECK_ANSWER_VALUES',
            CHECK_ANSWER_VALUES,
            _('Given maximum number of answers must be greater than minimum '
              'and both must be greater than one')
        )
    ]

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

    def _log_operation(self, method, data):
        message = 'RANDOM WIZARD LINE «{}» - {}: {}'

        name = self.name
        message = message.format(name, method, data)

        _logger.debug(message)

    def _append_in(self, domains, source, target, exclude, nm=False):
        """ Appends new domain to the given list. Later, these domains can be
        joined using OR or AND functions from odoo.osv.expression

        Arguments:
            domains {list} -- list to which new domain will be appened
            source {str} -- field name (in self) from which value will be taken
            target {str} -- field name will be used in new domain
            exclude {bool} -- use negative operator

        Keyword Arguments:
            nm {bool} -- True if target is a Many2many (default: {False})
        """

        source_ids = self.mapped('{}.id'.format(source))
        negation = getattr(self, exclude)

        if source_ids:
            if nm:
                operator = '!=' if negation else '='
            else:
                operator = 'not in' if negation else 'in'

            domain = [(target, operator, source_ids)]

            domains.append(domain)

    def _append_answers(self, domains):
        if self.number_of_answers:
            if self.exclude_answers:
                domain = [
                    '|',
                    ('answer_count', '<', self.minimum_answers),
                    ('answer_count', '>', self.maximum_answers)
                ]
            else:
                domain = [
                    ('answer_count', '>=', self.minimum_answers),
                    ('answer_count', '<=', self.maximum_answers)
                ]

            domains.append(domain)

    def _append_authorship(self, domains):
        """ Appends new domain to the given list with the needed leaft to allow
        filtering using athorship

        Arguments:
            domains {list} -- list to which new domain will be appened
        """

        if self.authorship:
            operator = '=' if self.authorship == 'own' else '!='
            domain = [('authorship', operator, True)]
            domains.append(domain)

    def _append_attachments(self, domains):
        """ Appends new domain to the given list with the needed leaft to allow
        filtering using attachments

        Arguments:
            domains {list} -- list to which new domain will be appened
        """

        if self.attachments:
            operator = '!=' if self.attachments == 'with' else '='
            domain = [('ir_attachment_ids', operator, False)]
            domains.append(domain)

    def _append_tests(self, domains):
        """ Appends new domain to the given list with the needed leaft to allow
        filtering using tests

        IMPORTANT: question_ids in test model and test_ids in question model
        really are 'academy.tests.question.rel' models.

        Arguments:
            domains {list} -- list to which new domain will be appened
        """

        training_ref = self.random_template_id.training_ref

        if self.tests_by_context:

            domain = False
            test_ids = False

            if training_ref:
                path = 'available_assignment_ids.test_id.question_ids.id'
                test_ids = training_ref.mapped(path)

            if test_ids:
                operator = 'not in' if self.exclude_tests else 'in'
                domain = [('test_ids', operator, test_ids)]
            elif not self.exclude_tests:
                domain = FALSE_DOMAIN

            if domain:
                domains.append(domain)
        else:
            self._append_in(domains, 'test_ids.question_ids', 'test_ids',
                            'exclude_tests', nm=True)

    def _append_questions(self, domains):
        """ Appends new domain to the given list with the needed leaft to allow
        filtering using questions

        Arguments:
            domains {list} -- list to which new domain will be appened
        """

        self.ensure_one()

        training_ref = self.random_template_id.training_ref

        if self.questions_by_context:

            domain = False
            question_ids = False

            if training_ref:
                question_set = training_ref.available_question_ids
                question_ids = question_set.mapped('id')

            if question_ids:
                operator = 'not in' if self.exclude_questions else 'in'
                domain = [('id', operator, question_ids)]
            elif not self.exclude_questions:
                domain = FALSE_DOMAIN

            if domain:
                domains.append(domain)
        else:
            self._append_in(
                domains, 'question_ids', 'id', 'exclude_questions')

    @staticmethod
    def _accumulate_domain(base_domain, accumulate_ids):
        if accumulate_ids:
            domain = AND([base_domain, [('id', 'not in', accumulate_ids)]])
        else:
            domain = base_domain.copy()

        return domain

    def _compute_domain(self, extra):
        """ Make two valid domains for record, one without restrictions and
        another with them.

        Arguments:
            extra {list} -- Normalized domain will be merged with an AND

        Returns:
            tuple -- both domains (common, restricted) in a tuple
        """

        domains = [
            [('depends_on_id', '=', False)],
            [('status', '=', 'ready')]
        ]

        domains.append(extra)

        self._append_in(domains, 'type_ids', 'type_id', 'exclude_types')
        self._append_in(domains, 'level_ids', 'level_id', 'exclude_levels')
        self._append_in(domains, 'owner_ids', 'owner_id', 'exclude_owners')
        self._append_in(domains, 'tag_ids', 'tag_ids', 'exclude_tags', nm=True)

        self._append_answers(domains)
        self._append_authorship(domains)
        self._append_attachments(domains)

        self._append_tests(domains)
        self._append_questions(domains)

        if self.categorization_ids:
            exclude = self.exclude_categorization
            categorization_ids = self.categorization_ids

            categorization = categorization_ids.get_domain(exclude)
            domains.append(categorization)

        return AND(domains)

    def compute_domains(self, extra, training_ref):
        """ Execute _compute_domain over all lines in the recordset.

        Arguments:
            extra {list} -- Normalized domain will be merged with an AND

        Returns:
            list -- list with one domain by each line in record
        """
        domains = []

        for record in self:
            domain = self._compute_domain(extra)
            domains.append(domain)

        return domains

    def _perform_search(self, extra):
        """ Performs search for a single template record, that is why the first
        line is an ``ensure_one``.

        Args:
            extra (list): Odoo valid domain will be merged as extra leafs in
            new computed domain (default: {None})

        Returns:
            recordset:  found question recordset for this single line
        """

        self.ensure_one()

        question_set = self.env['academy.tests.question']
        if self.quantity <= 0:
            return question_set

        ctx = {'sort_by_random': True}
        question_set = question_set.with_context(ctx)

        domain = self._compute_domain(extra)
        self._log_operation('_perform_search', domain)

        return question_set.search(domain, limit=self.quantity)

    def perform_search(self, extra=None):
        """ Performs search for all lines in given recorset. This method
        calls a private ``_perform_search`` method by earch record.

        This uses resulted question IDs to exclude them when it will perform
        the next line search

        Keyword Arguments:
            extra {list} -- Odoo valid domain will be merged as extra leafs in
            new computed domain (default: {None})
            random {bool} -- True to allow return found questions when the
            required quantity has not been reached

        Returns:
            recordset -- found question recordset using all lines
        """

        result_set = self.env['academy.tests.question']
        base_domain = (extra or []).copy()
        accumulate_ids = []

        for record in self:
            domain = self._accumulate_domain(base_domain, accumulate_ids)
            record_set = record._perform_search(domain)

            accumulate_ids.extend(record_set.mapped('id'))
            if accumulate_ids:
                domain = AND([extra, [('id', 'not in', accumulate_ids)]])

            result_set += record_set

        return result_set

    def perform_search_count(self, extra=None, training_ref=None):
        self.ensure_one()

        if not training_ref:
            training_ref = self.random_template_id.training_ref

        question_set = self.env['academy.tests.question']
        domain = self._compute_domain(extra or [])

        self._log_operation('perform_search_count', domain)

        return question_set.search_count(domain)
