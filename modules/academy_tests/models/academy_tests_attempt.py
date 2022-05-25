# -*- coding: utf-8 -*-
""" AcademyTestsAttempt

This module contains the academy.tests.attempt Odoo model which stores
all academy tests attempt attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import odoo.addons.academy_base.models.utils.custom_model_fields as custom
from .utils.sql_inverse_searches import ATTEMPTS_CLOSED_SEARCH
from .utils.sql_inverse_searches import REQUEST_ATTEMPT_PASSED_SEARCH
from odoo.osv.expression import FALSE_DOMAIN, TRUE_DOMAIN
# from .utils.sql_m2m_through_view import \
#     ACADEMY_TESTS_ATTEMPT_TRAINING_ACTION_REL
# from .utils.sql_m2m_through_view import \
#     ACADEMY_TESTS_ATTEMPT_TRAINING_ACTIVITY_REL
# from .utils.sql_m2m_through_view import \
#     ACADEMY_TESTS_ATTEMPT_TRAINING_MODULE_REL

from logging import getLogger
from datetime import datetime

_logger = getLogger(__name__)


class AcademyTestsAttempt(models.Model):
    """ Logs an attempt by a user to solve a test
    """

    _name = 'academy.tests.attempt'
    _description = u'Academy tests attempt'

    _rec_name = 'id'
    _order = 'start ASC'

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Check it to show this attempt or uncheck to archivate'
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this attempt',
        translate=True
    )

    student_id = fields.Many2one(
        string='Student',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose the student who performs the attempt',
        comodel_name='academy.student',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    test_id = fields.Many2one(
        string='Test',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose test to be attempted',
        comodel_name='academy.tests.test',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    start = fields.Datetime(
        string='Start',
        required=True,
        readonly=False,
        index=False,
        default=fields.datetime.now(),
        help='Choose date and time to start the attempt'
    )

    elapsed = fields.Float(
        string='Elapsed time',
        required=True,
        readonly=False,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Enter the time has been used in attempt'
    )

    available = fields.Float(
        string='Available time',
        required=True,
        readonly=False,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Enter the total time for the attempt'
    )

    end = fields.Datetime(
        string='End',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose date and time the attempt ended'
    )

    correction_type = fields.Selection(
        string='Correction type',
        required=True,
        readonly=False,
        index=False,
        default='test',
        help='Choose the type of attempt',
        selection=[('question', 'By question'), ('test', 'By test')]
    )

    attempt_answer_ids = fields.One2many(
        string='Answers',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Links all answer attempts',
        comodel_name='academy.tests.attempt.answer',
        inverse_name='attempt_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None,
        copy=True,
    )

    # This must be a Many2manyThroughView because middle relation is a VIEW
    attempt_final_answer_ids = custom.Many2manyThroughView(
        string='Final answers',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.attempt.answer',
        relation='academy_tests_attempt_final_answer_helper',
        column1='attempt_id',
        column2='attempt_answer_id',
        domain=[],
        context={},
        limit=None,
        copy=False,
    )

    right = fields.Float(
        string='Right (awarded)',
        required=True,
        readonly=False,
        index=False,
        default=1.0,
        digits=(16, 2),
        help='Score by right question'
    )

    wrong = fields.Float(
        string='Wrong (awarded)',
        required=True,
        readonly=False,
        index=False,
        default=-1.0,
        digits=(16, 2),
        help='Score by wrong question'
    )

    blank = fields.Float(
        string='Blank (awarded)',
        required=True,
        readonly=False,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Score by blank question'
    )

    lock_time = fields.Boolean(
        string='Lock time',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help=('Check to not allow the user to continue with the test once '
              'the time has passed')
    )

    closed = fields.Boolean(
        string='Closed',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Attempt has finished and it has been fully stored',
        compute=lambda self: self._compute_closed(),
        search='_closed_search'
    )

    @api.depends('elapsed', 'end', 'attempt_answer_ids')
    def _compute_closed(self):
        for record in self:
            answered_set = record._get_anwered_link_ids()
            test_set = record._get_tests_link_ids()
            left_set = test_set - answered_set

            record.closed = record.elapsed and record.end and not left_set

    @api.model
    def _closed_search(self, operator, operand):
        self.env.cr.execute(ATTEMPTS_CLOSED_SEARCH)
        result_set = self.env.cr.fetchall()

        assert operator in ['=', '!='] and operand in [True, False], \
            _('Invalid search operation for closed field in attempt')

        if result_set:
            ids = [item[0] for item in result_set]

            if self._closed_is_true(operator, operand):
                domain = [('id', 'in', ids)]
            else:
                domain = [('id', 'not in', ids)]
        else:
            if self._closed_is_true(operator, operand):
                domain = FALSE_DOMAIN
            else:
                domain = TRUE_DOMAIN

        return domain

    _sql_constraints = [(
        'check_start_before_end',
        'CHECK("end" IS NULL OR start <= "end")',
        _(u'The start date/time must be anterior to the end date')
    )]

    @staticmethod
    def _closed_is_true(operator, value):
        return operator == '=' and value or operator == '!=' and not value

    def _get_anwered_link_ids(self):
        field_path = 'attempt_answer_ids.question_link_id'
        return self.mapped(field_path)

    def _get_tests_link_ids(self):
        field_path = 'test_id.question_ids'
        return self.mapped(field_path)

    def close(self):
        """ Close attempt performing the following actions:
        - Set end value to current datetime if it's empty
        - Computes elapsed time value if end has not been set
        - Appends an attempt answer line for each of the questions have not
        been answered
        """

        for record in self:
            if not record.end:
                value = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                record.end = value

            if not record.elapsed:
                end = fields.Datetime.from_string(record.end)
                start = fields.Datetime.from_string(record.start)
                elapsed = (end - start).total_seconds() / 60
                record.elapsed = min(record.available, elapsed)

            answered_set = record._get_anwered_link_ids()
            test_set = record._get_tests_link_ids()

            answer_obj = record.env['academy.tests.attempt.answer']
            left_set = test_set - answered_set
            for link_item in (left_set):
                values = {
                    'active': True,
                    'user_action': 'blank',
                    'attempt_id': record.id,
                    'question_link_id': link_item.id,
                    'answer_id': None
                }
                answer_obj.create(values)

            self.closed = True

    @api.depends('student_id', 'test_id')
    def name_get(self):
        result = []
        for record in self:
            if isinstance(record.id, models.NewId):
                name = _('New attempt')
            else:
                student = record.student_id.name or _('Student')
                test = record.test_id.name or _('Test')
                name = '{} - {} - #{}'.format(student, test, record.id)

            result.append((record.id, name))

        return result

    # ------------------------- RELATED TEST FIELDS ---------------------------

    tag_ids = fields.Many2many(
        string='Tags',
        readonly=False,
        related='test_id.tag_ids'
    )

    topic_ids = custom.Many2many(
        string='Topics',
        readonly=True,
        related='test_id.topic_ids'
    )

    # ------------------------ RELATED RESUME FIELDS --------------------------

    resume_id = fields.Many2one(
        string='Resume',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.attempt.resume.helper',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        compute='_compute_resume_id'
    )

    @api.depends('test_id')
    def _compute_resume_id(self):
        resume_obj = self.env['academy.tests.attempt.resume.helper']

        for record in self:
            record.resume_id = resume_obj.browse(record.id)

    questions = fields.Integer(
        string='Questions',
        related='resume_id.questions',
        help='Number of questions in test'
    )

    answered = fields.Integer(
        string='Answered',
        related='resume_id.answered',
        help='Number of final answered questions'
    )

    right_count = fields.Integer(
        string='Right',
        related='resume_id.right',
        help='Number of final right answers'
    )

    wrong_count = fields.Integer(
        string='Wrong',
        related='resume_id.wrong',
        help='Number of final wrong answers'
    )

    answer_count = fields.Integer(
        string='Answer',
        related='resume_id.answer',
        help='Number of final answers marked as answered'
    )

    doubt_count = fields.Integer(
        string='Doubt',
        related='resume_id.doubt',
        help='Number of final answers marked as doubt'
    )

    right_points = fields.Float(
        string='Right points',
        related="resume_id.right_points",
        help='Final score obtained based on right answers'
    )

    wrong_points = fields.Float(
        string='Wrong points',
        related="resume_id.wrong_points",
        help='Final score obtained based on wrong answers'
    )

    blank_points = fields.Float(
        string='Blank points',
        related="resume_id.blank_points",
        help='Final score obtained based on blank answers'
    )

    final_points = fields.Float(
        string='Final points',
        related="resume_id.final_points",
        help='Final attempt score'
    )

    max_points = fields.Float(
        string='Maximum points',
        related="resume_id.max_points",
        help='Maximum number of points the student can obtain'
    )

    passed = fields.Boolean(
        string='Passed',
        required=False,
        readonly=True,
        index=False,
        default=False,
        help=('True if the final points are greater than or equal to half of '
              'the total score'),
        compute='_compute_passed',
        search='_search_passed'
    )

    @api.depends('test_id')
    def _compute_passed(self):
        for record in self:
            record.passed = record.final_points >= (record.max_points / 2.0)

    def _search_passed(self, operator, value):
        result_domain = FALSE_DOMAIN

        where_value = value if operator == '=' else not value
        query = REQUEST_ATTEMPT_PASSED_SEARCH.format(where_value)

        self.env.cr.execute(query)
        rows = self.env.cr.dictfetchall()
        if rows:
            ids = [row['id'] for row in rows]
            result_domain = [('id', 'in', ids)]
            print(result_domain)

        return result_domain

    # ------------------------ RELATED TRAINING ITEMS -------------------------

    training_action_ids = fields.Many2many(
        string='Training actions',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Allow users to search attempts by training action',
        comodel_name='academy.training.action',
        relation='academy_tests_attempt_training_action_rel',
        column1='attempt_id',
        column2='training_action_id',
        domain=[],
        context={},
        limit=None,
        compute='_compute_training_action_ids',
        search='_search_training_action_ids'
    )

    @api.depends('test_id')
    def _compute_training_action_ids(self):
        for record in self:
            ids = record.mapped('test_id.training_action_ids.id')
            if ids:
                record.training_action_ids = [(6, 0, ids)]
            else:
                record.training_action_ids = [(5, 0, 0)]

    def _search_training_action_ids(self, operator, value):
        domain = FALSE_DOMAIN

        action_set = self.env['academy.training.action']
        action_domain = [('action_name', operator, value)]
        action_set = action_set.search(action_domain)

        if action_set:
            test_ids = action_set.mapped('test_ids.id')
            domain = [('test_id', 'in', test_ids)]

        return domain

    training_activity_ids = fields.Many2many(
        string='Training activities',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Allow users to search attempts by training activity',
        comodel_name='academy.training.activity',
        relation='academy_tests_attempt_training_activity_rel',
        column1='attempt_id',
        column2='training_activity_id',
        domain=[],
        context={},
        limit=None,
        compute='_compute_training_activity_ids',
        search='_search_training_activity_ids'
    )

    @api.depends('test_id')
    def _compute_training_activity_ids(self):
        for record in self:
            ids = record.mapped('test_id.training_activity_ids.id')
            if ids:
                record.training_activity_ids = [(6, 0, ids)]
            else:
                record.training_activity_ids = [(5, 0, 0)]

    def _search_training_activity_ids(self, operator, value):
        domain = FALSE_DOMAIN

        activity_set = self.env['academy.training.activity']
        activity_domain = [('name', operator, value)]
        activity_set = activity_set.search(activity_domain)

        if activity_set:
            test_ids = activity_set.mapped('test_ids.id')
            domain = [('test_id', 'in', test_ids)]

        return domain

    competency_unit_ids = fields.Many2many(
        string='Competency units',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Allow users to search attempts by competency units',
        comodel_name='academy.training.module',
        relation='academy_tests_attempt_competency_unit_rel',
        column1='attempt_id',
        column2='competency_unit_id',
        domain=[],
        context={},
        limit=None,
        compute='_compute_competency_unit_ids',
        search='_search_competency_unit_ids'
    )

    @api.depends('test_id')
    def _compute_competency_unit_ids(self):
        for record in self:
            ids = record.mapped('test_id.competency_unit_ids.id')
            if ids:
                record.competency_unit_ids = [(6, 0, ids)]
            else:
                record.competency_unit_ids = [(5, 0, 0)]

    def _search_competency_unit_ids(self, operator, value):
        domain = FALSE_DOMAIN

        competency_set = self.env['academy.competency.unit']
        competency_domain = [('competency_name', operator, value)]
        competency_set = competency_set.search(competency_domain)

        if competency_set:
            test_ids = competency_set.mapped('competency_test_ids.id')
            domain = [('test_id', 'in', test_ids)]

        return domain

    training_module_ids = fields.Many2many(
        string='Training modules',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Allow users to search attempts by training module',
        comodel_name='academy.training.module',
        relation='academy_tests_attempt_training_module_rel',
        column1='attempt_id',
        column2='training_module_id',
        domain=[],
        context={},
        limit=None,
        compute='_compute_training_module_ids',
        search='_search_training_module_ids'
    )

    @api.depends('test_id')
    def _compute_training_module_ids(self):
        for record in self:
            ids = record.mapped('test_id.training_module_ids.id')
            if ids:
                record.training_module_ids = [(6, 0, ids)]
            else:
                record.training_module_ids = [(5, 0, 0)]

    def _search_training_module_ids(self, operator, value):
        domain = FALSE_DOMAIN

        module_set = self.env['academy.training.module']
        module_domain = [('name', operator, value)]
        module_set = module_set.search(module_domain)

        if module_set:
            test_ids = module_set.mapped('test_ids.id')
            domain = [('test_id', 'in', test_ids)]

        return domain

    test_owner_id = fields.Many2one(
        string='Test owner',
        readonly=True,
        related="test_id.owner_id"
    )
