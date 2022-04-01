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
from enum import Enum


_logger = getLogger(__name__)


WIZARD_LINE_STATES = [
    ('step1', _('General')),
    ('step2', _('Categorization')),
    ('step3', _('Tests')),
    ('step4', _('Questions')),
    ('step5', _('Special'))
]

RESTRICT_BY = [
    ('answer', _('Answered')),
    ('wrong', _('Mistaken')),
    ('blank', _('Blank')),
    ('doubt', _('Doubt')),
    ('answer_doubt', _('Answered/Doubt')),
    ('blank_wrong', _('Mistaken/Blank')),
    ('doubt_wrong', _('Mistaken/Doubt')),
    ('blank_doubt', _('Blank/Doubt')),
    ('blank_doubt_wrong', _('Mistaken/Blank/Doubt'))
]

ACTION_MODEL = 'academy.training.action'
ENROLMENT_MODEL = 'academy.training.action.enrolment'
STATS_MODEL = 'academy.statistics.student.question.readonly'

CHECK_ANSWER_VALUES = ('CHECK(minimum_answers > 1 AND maximum_answers > 1 AND '
                       'minimum_answers <= maximum_answers)')


class LogDomain(Enum):
    NONE = 0
    STOCK = 1
    ANSWERED = 3
    RESTRICTED = 5
    FINAL = 9


# pylint: disable=locally-disabled, R0903, W0212
class AcademyTestsRandomWizardLine(models.Model):
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

    # ----------- SETUP REQUERIMENTS ------------

    stock_by = fields.Selection(
        string='Stock by',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose how minimum question stock will be computed',
        selection=[
            ('pct', 'Percent')
        ]
    )

    stock = fields.Float(
        string='Stock',
        required=True,
        readonly=False,
        index=False,
        default=1.0,
        digits=(16, 2),
        help='Minimum number of questions required to make new test'
    )

    answered_by = fields.Selection(
        string='Raised by',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose how minimum answered questions will be computed',
        selection=[
            ('pct', 'Percent')
        ]
    )

    answered = fields.Float(
        string='Raised',
        required=True,
        readonly=False,
        index=False,
        default=1.0,
        help='Minimum number of answered questions required to make new test'
    )

    restrict_by = fields.Selection(
        string='Restrict by',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=('Choose how the minimum number of questions will be calculated, '
              'according to the given restriction'),
        selection=RESTRICT_BY
    )

    supply = fields.Float(
        string='Supply',
        required=True,
        readonly=False,
        index=False,
        default=1.0,
        help=('Minimum number of  mistakes/doubts/blanks required to '
              'make new test')
    )

    ratio = fields.Float(
        string='Ratio',
        required=True,
        readonly=False,
        index=False,
        default=0.5,
        digits=(16, 2),
        help=('Percentaje of mistakes/doubts/blanks required to use a '
              'question in test')
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

    def _get_context_ref(self):
        self.ensure_one()
        return self.random_template_id.context_ref

    def _is_an_action(self, item):
        return isinstance(item, type(self.env['academy.training.action']))

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

    def _append_tests(self, domains, context_ref):
        """ Appends new domain to the given list with the needed leaft to allow
        filtering using tests

        IMPORTANT: question_ids in test model and test_ids in question model
        really are 'academy.tests.question.rel' models.

        Arguments:
            domains {list} -- list to which new domain will be appened
        """

        if self.tests_by_context:

            domain = False
            test_ids = False

            if context_ref:
                path = 'available_test_ids.question_ids.id'
                test_ids = context_ref.mapped(path)

            if test_ids:
                operator = '!=' if self.exclude_tests else '='
                domain = [('test_ids', operator, test_ids)]
            elif not self.exclude_tests:
                domain = FALSE_DOMAIN

            if domain:
                domains.append(domain)
        else:
            self._append_in(domains, 'test_ids.question_ids', 'test_ids',
                            'exclude_tests', nm=True)

    def _append_questions(self, domains, context_ref):
        """ Appends new domain to the given list with the needed leaft to allow
        filtering using questions

        Arguments:
            domains {list} -- list to which new domain will be appened
        """

        if self.questions_by_context:

            domain = False
            question_ids = False

            if context_ref:

                if self._is_an_action(context_ref):
                    path = 'training_activity_id.available_question_ids.id'
                else:
                    path = 'training_module_ids.available_question_ids.id'

                question_ids = context_ref.mapped(path)

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

    def _compute_domain(self, extra, context_ref):
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

        self._append_tests(domains, context_ref)
        self._append_questions(domains, context_ref)

        if self.categorization_ids:
            exclude = self.exclude_categorization
            categorization_ids = self.categorization_ids

            categorization = categorization_ids.get_domain(exclude)
            domains.append(categorization)

        return AND(domains)

    def compute_domains(self, extra, context_ref):
        """ Execute _compute_domain over all lines in the recordset.

        Arguments:
            extra {list} -- Normalized domain will be merged with an AND

        Returns:
            list -- list with one domain by each line in record
        """
        domains = []

        for record in self:
            domain = self._compute_domain(extra, context_ref)
            domains.append(domain)

        return domains

    def _get_student_ids_from_context(self, context_ref):
        """ Reads context field from template, and maps the ID of the all
        students.

        NOTE: context can be an action or an enrolment

        Returns:
            list -- list of ID's of the all students from the context item
        """

        student_ids = []

        if context_ref:

            if self._is_an_action(context_ref):
                enrolment_set = context_ref.training_action_enrolment_ids
            else:
                enrolment_set = context_ref

            if enrolment_set:
                student_ids = enrolment_set.mapped('student_id.id')

        return student_ids

    def _log_operation(self, data, restrict):
        message = 'RANDOM WIZARD LINE «{}» - {}: {}'

        name = self.name

        if restrict == LogDomain.STOCK:
            message = message.format(name, 'Checking stock', data)

        if restrict == LogDomain.ANSWERED:
            message = message.format(name, 'Checking answered', data)

        elif restrict == LogDomain.RESTRICTED:
            message = message.format(name, 'Checking restrictions', data)

        elif restrict == LogDomain.FINAL:
            message = message.format(name, 'Perform final search', data)

        else:
            message = message.format(name, 'Other', data)

        _logger.debug(message)

    def _statistics_domain(self, context_ref):
        """ Use academy.statistics.student.question.readonly to get the ID only
        from those questions whose student is in a given context. Then use this
        ID's to make a domain like [('id', 'in', ids)] which can be used with
        academy.tests.question.

        If context is not set, all statistics will be used to build the domain.

        Arguments:
            domain {list} -- Odoo valid domain which will be extended with the
            new created

        Returns:
            list -- Odoo valid domain (given domain & new created)
        """

        if context_ref:

            student_ids = self._get_student_ids_from_context(context_ref)
            if student_ids:
                result = [('student_id', 'in', student_ids)]

            else:
                _logger.debug(_('There are no students in the given context'))
                result = FALSE_DOMAIN

        else:
            _logger.debug(_('There is no context to apply restrictions'))
            result = TRUE_DOMAIN

        self._log_operation(result, LogDomain.ANSWERED)

        return result

    def _get_stock(self, domain):
        """ Uses non restricted domain to search all available questions.

        Later resut will be used to compute percents in restrictions.

        Arguments:
            domain {list} -- Odoo valid domain

        Returns:
            int -- number of records has been found
        """

        question_set = self.env['academy.tests.question']

        self._log_operation(domain, LogDomain.STOCK)
        quantity = question_set.search_count(domain)

        return quantity or 0

    def _assert_stock(self, quantity):
        """ Check if are there enough questions to supply the given percentage

        Arguments:
            quantity {int} -- Total number of questions, without restrictions
        """

        if not quantity >= (self.stock * self.quantity):
            raise UserError(_('Not enough questions in stock'))

    @staticmethod
    def _start_counting(result_set):
        """ Initialize the counters will be needed to log given restrictions

        Arguments:
            result_set {recordset} -- Full statistics recordset

        Returns:
            tuple -- all the needed initial values
        """
        return 0, 0, len(result_set)

    @staticmethod
    def _finish_counting(total, meets, fails, ratio):
        """ Collects the values from all counters related with restrictions to
        create a text string to display them

        Arguments:
            total {int} -- Full statistics recordset length (no resticted)
            meets {float} -- meets rate
            fails {float} -- fails rate
            ratio {float} -- given ratio field value for self

        Returns:
            str -- message to present all given values
        """

        msg = _('{} aggregate records have been retrieved, {:.2f}% are '
                'greater or equal to {:.2f} and {:.2f}% are less than it')

        meets = meets / total * 100
        fails = fails / total * 100
        ratio = ratio * 100

        return msg.format(total, meets, ratio, fails)

    def _read_question_ids(self, result_set, ratio=False):
        """ Read question_id column from given aggregate (read_group) results

        Arguments:
            result_set {recordset} -- aggregate (read_group) recordset

        Keyword Arguments:
            ratio {mixed} -- ratio that must exceed the computed value from
            the given records (default: {False})

        Returns:
            list -- list with the obtained IDs. All the values will be unique.
        """

        results = []

        if ratio is not False and ratio >= 0:
            meets, fails, total = self._start_counting(result_set)

            for item in result_set:
                if item['computed'] >= ratio:
                    results.append(item['question_id'][0])
                    meets += 1
                else:
                    fails += 1

            msg = self._finish_counting(total, meets, fails, ratio)
            self._log_operation(msg, LogDomain.RESTRICTED)

        else:
            for item in result_set:
                results.append(item['question_id'][0])

        return list(set(results)) if results else []

    def _assert_answer(self, domain, quantity):
        """ Check if are there enough answered questions to supply the given
        percentaje

        Arguments:
            domain {list} -- Odoo valid domain
            quantity {int} -- Total number of questions, without restrictions
        """

        statistics_set = self.env[STATS_MODEL]

        statistics_set = statistics_set.read_group(
            domain, ['question_id'], ['question_id'], lazy=False)

        results = self._read_question_ids(statistics_set, ratio=False)

        if not len(statistics_set) >= (self.answered * quantity):
            raise UserError(_('Not enough questions answered'))

        return results

    def _assert_restricted(self, domain, quantity):
        """ Check if are there enough questions that meet the constraints, to
        supply the given percentaje

        Arguments:
            domain {list} -- Odoo valid domain
            quantity {int} -- Total number of questions, without restrictions

        Returns:
            list -- Odoo domain has been used to perform the search
        """

        statistics_set = self.env[STATS_MODEL]

        field = 'computed:avg({}_percent)'.format(self.restrict_by)
        statistics_set = statistics_set.read_group(
            domain, [field], ['question_id'], lazy=False)

        results = self._read_question_ids(statistics_set, self.ratio)

        if not len(results) >= (self.supply * quantity):
            msg = _('The ratio indicated in the restrictions is not reached')
            raise UserError(msg)

        return results

    def _assert_restrictions(self, domain, context_ref):
        available = self._get_stock(domain)

        if self.stock_by == 'pct':
            self._assert_stock(available)

        if self.answered_by or self.restrict_by:
            statistics = self._statistics_domain(context_ref)

            if self.answered_by:
                question_ids = self._assert_answer(statistics, available)

            if self.restrict_by:
                question_ids = self._assert_restricted(statistics, available)

            if question_ids:
                domain = AND([domain, [('id', 'in', question_ids)]])

    def _perform_search(self, extra, context_ref):
        """ Performs search for a single template record, that is why the first
        line is an ``ensure_one``.

        This method will be calle for each record from the ``perform_search``
        public method.

        Keyword Arguments:
            extra {list} -- Odoo valid domain will be merged as extra leafs in
            new computed domain (default: {None})
            random {bool} -- True to use SORT BY RANDOM() (default: {True})

        Returns:
            recordset -- found question recordset for this single line
        """

        self.ensure_one()

        question_set = self.env['academy.tests.question']

        ctx = {'sort_by_random': True}
        question_set = question_set.with_context(ctx)

        domain = self._compute_domain(extra, context_ref)
        self._assert_restrictions(domain, context_ref)

        self._log_operation(domain, LogDomain.FINAL)

        return question_set.search(domain, limit=self.quantity)

    @staticmethod
    def _initialize_domains(extra):
        if not isinstance(extra, (list, tuple)):
            extra = []

        domain = extra.copy()

        return extra, domain

    def _assert_expected_questions(self, record_set, allow_partial):
        msg = _('RANDOM WIZARD LINE «{}»: There is not enough questions')

        if not allow_partial and len(record_set) != self.quantity:
            raise UserError(msg.format(self.name))

    def perform_search(
            self, extra=None, context_ref=None, allow_partial=False):
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

        ids = []
        extra, domain = self._initialize_domains(extra)

        for record in self:
            record_set = record._perform_search(domain, context_ref)

            record._assert_expected_questions(record_set, allow_partial)
            ids.extend(record_set.mapped('id'))
            if ids:
                domain = AND([extra, [('id', 'not in', ids)]])

            result_set += record_set

        return result_set

    def perform_search_count(self, extra=None, context_ref=None):
        self.ensure_one()

        if not context_ref:
            context_ref = self.random_template_id.context_ref

        question_set = self.env['academy.tests.question']
        domain = self._compute_domain(extra or [], context_ref)

        self._log_operation(domain, LogDomain.FINAL)

        return question_set.search_count(domain)

    def build_link_operations(
            self, extra=None, context_ref=None, allow_partial=False):
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

        ids = []
        extra, domain = self._initialize_domains(extra)

        request_id = self.env.context.get('request_id', None)

        operations = []
        sequence = 10

        for record in self:
            record_set = record._perform_search(domain, context_ref)

            record._assert_expected_questions(record_set, allow_partial)
            ids.extend(record_set.mapped('id'))
            if ids:
                domain = AND([extra, [('id', 'not in', ids)]])

            if record.test_block_id:
                test_block_id = record.test_block_id.id
            else:
                test_block_id = None

            for question_item in record_set:
                link = {
                    'sequence': sequence,
                    'question_id': question_item.id,
                    'request_id': request_id,
                    'test_block_id': test_block_id
                }
                operations.append((0, None, link))
                sequence += 10

        return operations
