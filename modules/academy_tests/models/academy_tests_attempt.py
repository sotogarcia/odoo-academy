# -*- coding: utf-8 -*-
""" AcademyTestsAttemptAnswer

This module contains the academy.tests.attempt.answer Odoo model which stores
all academy tests attempt answer attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.translate import _
from odoo.tools import safe_eval
from odoo.osv.expression import TRUE_DOMAIN
from odoo.exceptions import ValidationError, UserError

from logging import getLogger
from psycopg2.errors import SerializationFailure
from datetime import timedelta, time
from math import floor
from sys import maxsize
from time import sleep

_logger = getLogger(__name__)

MAX_RETRIES = 5


class AcademyTestAttempt(models.Model):
    """ Logs all student answers in a test attempt, even if later he
    change it by another answer
    """

    _name = 'academy.tests.attempt'
    _description = u'Academy tests attempt'

    _rec_name = 'id'
    _order = 'start DESC'

    _check_company_auto = True

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this attempt',
        translate=True
    )

    prevalence = fields.Integer(
        string='Prevalence',
        required=False,
        readonly=True,
        index=False,
        default=9999,
        help='Rank of the attempts by assignment and user'
    )

    rank = fields.Integer(
        string='Rank',
        required=True,
        readonly=True,
        index=True,
        default=9999,
        help='Rank of the attempts by assignment'
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Check it to show this attempt or uncheck to archivate'
    )

    individual_id = fields.Many2one(
        string='Individual assignment',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=False,
        comodel_name='academy.tests.test.training.assignment.enrolment.rel',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    company_id = fields.Many2one(
        string='Company',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Available for company',
        comodel_name='res.company',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        related='individual_id.company_id',
        store=True
    )

    assignment_id = fields.Many2one(
        string='Assignment',
        index=True,
        readonly=True,
        related='individual_id.assignment_id',
        store=True
    )

    test_id = fields.Many2one(
        string='Test',
        index=True,
        readonly=True,
        related='individual_id.assignment_id.test_id',
        store=True
    )

    enrolment_id = fields.Many2one(
        string='Enrolment',
        index=True,
        readonly=True,
        related='individual_id.enrolment_id',
        store=True
    )

    student_id = fields.Many2one(
        string='Student',
        index=True,
        readonly=True,
        related='individual_id.enrolment_id.student_id',
        store=True
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
        digits=(16, 10),
        help='Enter the time has been used in attempt'
    )

    available_time = fields.Float(
        string='Available time',
        required=True,
        readonly=False,
        index=False,
        default=0.0,
        digits=(16, 10),
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

    time_by = fields.Selection(
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

    attempt_answer_count = fields.Integer(
        string='Total answers',
        required=True,
        readonly=True,
        index=True,
        default=0,
        help='Total number of user\'s answers to this attempt',
        compute='_compute_attempt_answer_count'
    )

    @api.depends('attempt_answer_ids')
    def _compute_attempt_answer_count(self):
        for record in self:
            record.attempt_answer_count = len(record.attempt_answer_ids)

    attempt_final_answer_ids = fields.One2many(
        string='Final answers',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Links to the attempt final answers',
        comodel_name='academy.tests.attempt.answer',
        inverse_name='attempt_id',
        domain=[('prevalence', '=', 1)],
        context={},
        auto_join=False,
        limit=None,
        copy=False,
    )

    right = fields.Float(
        string='Right (awarded)',
        required=True,
        readonly=False,
        index=False,
        default=1.0,
        digits=(16, 10),
        help='Score by right question'
    )

    wrong = fields.Float(
        string='Wrong (awarded)',
        required=True,
        readonly=False,
        index=False,
        default=-1.0,
        digits=(16, 10),
        help='Score by wrong question'
    )

    blank = fields.Float(
        string='Blank (awarded)',
        required=True,
        readonly=False,
        index=False,
        default=0.0,
        digits=(16, 10),
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
        help='Attempt has finished and it has been fully stored'
    )

    training_action_id = fields.Many2one(
        string='Training action',
        related='individual_id.enrolment_id.training_action_id',
        store=True
    )

    training_activity_id = fields.Many2one(
        string='Training activity',
        related=('individual_id.enrolment_id.training_action_id.'
                 'training_activity_id'),
        store=True
    )

    # competency_unit_id = fields.Many2one(
    #     string='Competency unit',
    #     related='assignment_id.competency_unit_id',
    # )

    # training_module_id = fields.Many2one(
    #     string='Training module',
    #     related='assignment_id.training_module_id',
    # )

    # topic_ids = fields.Many2many(
    #     string='Topics',
    #     readonly=True,
    #     help='Topics from all the questions in the attempt',
    #     related='assignment_id.test_id.topic_ids'
    # )

    # tag_ids = fields.Many2many(
    #     string='Tags',
    #     readonly=True,
    #     help='Tag can be used to better describe this question',
    #     related='assignment_id.test_id.tag_ids'
    # )

    question_count = fields.Integer(
        string='Question count',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help='Total number of questions'
    )

    answered_count = fields.Integer(
        string='Anwered count',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help='The number of answered questions'
    )

    doubt_count = fields.Integer(
        string='Doubt count',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help='The number of questions that have been answered with doubt'
    )

    answer_count = fields.Integer(
        string='Answer count',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help='The number of final sure responses'
    )

    right_count = fields.Integer(
        string='Right count',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help='The number of right final answers'
    )

    wrong_count = fields.Integer(
        string='Wrong count',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help='The number of wrong final answers'
    )

    blank_count = fields.Integer(
        string='Blank count',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help='The number of blank final answers'
    )

    max_points = fields.Float(
        string='Max points',
        required=True,
        readonly=True,
        index=True,
        default=0.0,
        digits=(16, 10),
        help='Maximum score that can be obtained in the exercise'
    )

    final_points = fields.Float(
        string='Final points',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 10),
        help='Total points earned based on final answers'
    )

    right_points = fields.Float(
        string='Right points',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 10),
        help='Total points earned based on right final answers'
    )

    wrong_points = fields.Float(
        string='Wrong points',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 10),
        help='Total points earned based on wrong final answers'
    )

    blank_points = fields.Float(
        string='Blank points',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 10),
        help='Total points earned based on blank final answers'
    )

    answered_percent = fields.Float(
        string='Answered percent',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 10),
        help=('Percentage of questions that have been answered, regardless of '
              'correctness')
    )

    right_percent = fields.Float(
        string='Right percent',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 10),
        help=('Percentage of correctly answered questions out of the total '
              'number of questions')
    )

    wrong_percent = fields.Float(
        string='Wrong percent',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 10),
        help=('Percentage of incorrectly answered questions out of the total '
              'number of questions')
    )

    blank_percent = fields.Float(
        string='Blank percent',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 10),
        help=('Percentage of questions left unanswered out of the total '
              'number of questions')
    )

    passed = fields.Boolean(
        string='Passed',
        required=False,
        readonly=True,
        index=True,
        default=False,
        help='True if final score is greater or equal to 5.0, False otherwise'
    )

    final_score = fields.Float(
        string='Final score',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 10),
        help=('Total score earned based on final answers, calculated on a '
              'scale of 10')
    )

    right_score = fields.Float(
        string='Right score',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 10),
        help=('Total score earned based on right final answers, calculated on '
              'a scale of 10')
    )

    wrong_score = fields.Float(
        string='Wrong score',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 10),
        help=('Total score earned based on wrong final answers, calculated on '
              'a scale of 10')
    )

    blank_score = fields.Float(
        string='Blank score',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 10),
        help=('Total score earned based on blank final answers, calculated on '
              'a scale of 10')
    )

    rating = fields.Integer(
        string='Rating',
        required=False,
        readonly=False,
        index=False,
        default=0,
        help=('Final attempt score computed over 10 points and truncated to '
              'the nearest lower integer')
    )

    grade = fields.Selection(
        string='Grade',
        required=False,
        readonly=True,
        index=False,
        default='fail',
        help='Passed if the obtained score reaches half of the maximum score',
        selection=[
            ('pass', 'Passing'),
            ('fail', 'Failing')
        ]
    )

    last_signal = fields.Datetime(
        string='Last signal',
        required=True,
        readonly=True,
        index=False,
        default=fields.datetime.now(),
        help='Timestamp of the latest \'keep alive\' signal received.'
    )

    # -------------------------------------------------------------------------
    # Constraints
    # -------------------------------------------------------------------------

    _sql_constraints = [
        (
            'check_start_before_end',
            'CHECK("end" IS NULL OR start <= "end")',
            _(u'The start date/time must be anterior to the end date')
        ),
        (
            'positive_rank',
            'CHECK(rank > 0)',
            'Rank must be a positive number'
        ),
        (
            'positive_prevalence',
            'CHECK(prevalence > 0)',
            'Prevalence must be a positive number'
        ),
        (
            'end_date_before_closed',
            '''CHECK (
                (closed != TRUE AND "end" IS NULL)
                OR (closed = TRUE AND "end" IS NOT NULL)
            )''',
            'The record cannot be closed unless the end date is set.'
        )
    ]

    # -------------------------------------------------------------------------
    # Overridden Non-CRUD Methods
    # -------------------------------------------------------------------------

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

    # -------------------------------------------------------------------------
    # CRUD Methods and Their Helpers
    # -------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        """ Overridden method 'create'
        """

        # Prevent manually closed
        self._raise_if_closed_set(vals_list)

        # Populate values from the individual assignment
        self._update_values(vals_list)

        parent = super(AcademyTestAttempt, self)
        result = parent.create(vals_list)

        return result

    def write(self, values):
        """ Remove answer_id when user action is True
        """

        # Prevent manually closed
        self._raise_if_closed_set(values)

        parent = super(AcademyTestAttempt, self)
        result = parent.write(values)

        return result

    def unlink(self):
        """ Overridden method 'unlink'
        """

        parent = super(AcademyTestAttempt, self)
        result = parent.unlink()

        return result

    @api.model
    def _get_individual_from_values(self, values):
        individual_mod = 'academy.tests.test.training.assignment.enrolment.rel'
        individual_set = self.env[individual_mod]

        individual_id = values.get('individual_id', False)
        if individual_id:
            individual_set = individual_set.browse(individual_id)

        return individual_set

    @api.model
    def _get_scale_from_assignment(self, assignment):
        scale = assignment.correction_scale_id

        if not scale:
            scale_path = 'academy_tests.default_correction_scale_id'
            config_param_obj = self.env['ir.config_parameter'].sudo()
            scale = config_param_obj.get_param(scale_path)

        return scale

    @staticmethod
    def _update_scale_values(values, scale):
        values = values or {}
        fields = ['right', 'wrong', 'blank']

        for item in fields:
            if item not in values:
                values[item] = getattr(scale, item)

        return (values[item] for item in fields)

    @api.model
    def _update_values(self, vals_list):
        """
        Update various values from related models when creating records in the
        academy.tests.attempt model.

        This method is intended to set values that should only be established
        **during the record creation process**. It accepts either a dictionary
        or a list of dictionaries (`vals_list`). The values are updated based
        on relationships with other models, such as individuals, assignments,
        and scales.

        Args:
            vals_list (list or dict): A dictionary or a list of dictionaries
            containing the values to update.

        The method updates or sets the following fields:
        - 'question_count': The number of questions in the test.
        - 'max_points': The maximum possible score for the attempt, based on
          the number of questions and the points for correct answers.
        - 'time_by': The allowed time for the test, based on the assignment.
        - 'lock_time': The time when the attempt will be locked, based on
          the assignment.

        Assertions:
        - The number of questions must be a non-negative integer.
        - The points for correct answers ('right') must be numeric.

        Raises:
            AssertionError: If any of the above assertions are violated.
        """
        if isinstance(vals_list, dict):  # Single item
            vals_list = [vals_list]

        for values in vals_list:

            individual = self._get_individual_from_values(values)
            if not individual:
                continue

            assignment = individual.assignment_id
            scale = self._get_scale_from_assignment(assignment)
            if scale:
                self._update_scale_values(values, scale)

            if 'question_count' not in values:
                question_count = len(assignment.mapped('test_id.question_ids'))
                assert self._is_natural(question_count, allow_zero=True), \
                    'Number of questions must be a non-negative integer'
                values['question_count'] = question_count

            if 'max_points' not in values:
                right = values.get('right', None)
                assert isinstance(right, (int, float)), \
                    'Right points values must be numeric'
                values['max_points'] = \
                    values['question_count'] * right

            if 'time_by' not in values:
                values['time_by'] = assignment.time_by

            if 'lock_time' not in values:
                values['lock_time'] = assignment.lock_time

    def _is_natural(self, value, allow_zero=False):
        return isinstance(value, int) \
            and (value > 0 or (value == 0 and allow_zero))

    def _raise_if_closed_set(self, vals_list):
        if not self.env.context.get('attempt_close_enabled', False):

            if isinstance(vals_list, dict):  # Single item
                vals_list = [vals_list]

            for values in vals_list:
                if values.get('closed', False):
                    message = (
                        'The "closed" field cannot be set to True directly. '
                        'Use the "recalculate" or "close" methods instead.'
                    )
                    raise ValidationError(message)

    # -------------------------------------------------------------------------
    # Recalculate and close methods
    # -------------------------------------------------------------------------

    def _ctx_disable_update(self, action, default=False):
        return self.env.context.get(f'disable_{action}_update', default)

    @staticmethod
    def _safe_division(dividend, divisor, default=0):
        try:
            result = dividend / divisor
        except ZeroDivisionError:
            message = (f'Warning: Division by zero. '
                       f'Returning {default} as the result.')
            _logger.warning(message)
            result = default

        return result

    def get_computed_values(self):
        self.ensure_one()

        _logger.debug(f'Calculating values for test attempt ID {self.id}')

        values = {}

        link_path = 'individual_id.assignment_id.test_id.question_ids'
        answer_set = self.attempt_final_answer_ids

        values['question_count'] = len(self.mapped(link_path))
        values['answered_count'] = len(answer_set.filtered(
            lambda r: r.user_action != 'blank'
        ))
        values['doubt_count'] = len(answer_set.filtered(
            lambda r: r.user_action == 'doubt'
        ))

        values['answer_count'] = len(answer_set.filtered(
            lambda r: r.user_action == 'answer'
        ))

        values['right_count'] = len(answer_set.filtered(
            lambda r: r.is_correct
        ))
        values['wrong_count'] = len(answer_set.filtered(
            lambda r: not r.is_correct and r.user_action != 'blank'
        ))
        values['blank_count'] = (
            values['question_count'] - values['answered_count']
        )

        values['max_points'] = values['question_count'] * self.right
        values['right_points'] = values['right_count'] * self.right
        values['wrong_points'] = values['wrong_count'] * self.wrong
        values['blank_points'] = values['blank_count'] * self.blank
        values['final_points'] = (
            values['right_points']
            + values['wrong_points']
            + values['blank_points']
        )

        values['answered_percent'] = self._safe_division(
            values['answered_count'], values['question_count'])

        values['right_percent'] = self._safe_division(
            values['right_count'], values['question_count'])

        values['wrong_percent'] = self._safe_division(
            values['wrong_count'], values['question_count'])

        values['blank_percent'] = self._safe_division(
            values['blank_count'], values['question_count'])

        # Rule of three
        # x_points --- max_points     => x_score = x_points * 10 / max_points
        # x_score  --- 10
        # ---------------------------------------------------------------------
        factor = self._safe_division(10, values['max_points'])
        values['final_score'] = values['final_points'] * factor
        values['right_score'] = values['right_points'] * factor
        values['wrong_score'] = values['wrong_points'] * factor
        values['blank_score'] = values['blank_points'] * factor

        values['rating'] = floor(values['final_score'])
        values['passed'] = (values['final_score'] >= 5.0)
        values['grade'] = 'pass' if values['passed'] else 'fail'

        return values

    def _get_anwered_link_ids(self):
        field_path = 'attempt_final_answer_ids.question_link_id'
        return self.mapped(field_path)

    def _get_tests_link_ids(self):
        field_path = 'individual_id.assignment_id.test_id.question_ids'
        return self.mapped(field_path)

    def _update_values_with_missing_answers(self, values):
        self.ensure_one()

        attempt_answer_o2m_ops = []

        answered_set = self._get_anwered_link_ids()
        test_set = self._get_tests_link_ids()
        left_set = test_set - answered_set

        for link_item in (left_set):
            o2m_op = (0, 0, {
                'active': True,
                'user_action': 'blank',
                'attempt_id': self.id,
                'question_link_id': link_item.id,
                'answer_id': None,
                'prevalence': 1
            })

            attempt_answer_o2m_ops.append(o2m_op)

        if attempt_answer_o2m_ops:
            values['attempt_answer_ids'] = attempt_answer_o2m_ops

    def _update_time_values(self, values):
        self.ensure_one()

        date_start = fields.Datetime.from_string(self.start)

        if self.end:
            date_stop = fields.Datetime.from_string(self.end)
        else:
            now = fields.Datetime.now()
            date_stop = max(now, date_start)
            values['end'] = date_stop.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        if not self.elapsed or 'end' in values:
            seconds = (date_stop - date_start).total_seconds()
            elapsed = seconds / 3600
            values['elapsed'] = \
                min(self.available_time or float(maxsize), elapsed)

        return values

    def _log_closing(self):
        message = f'The following test attempts will be closed: {self.ids}.'
        _logger.info(message)

    def _filter_closed_records(self, warning=True):
        if warning:
            opened_set = self.filtered(lambda r: not r.closed)
            if opened_set:
                _logger.warning(f'Open test attempts {opened_set.ids} will be '
                                f'ignored during recalculation.')

        return self.filtered(lambda r: r.closed)

    def recalculate(self, close=False):
        """
        Recalculates and optionally closes the attempt records based on the
        `close` flag.

        Args:
            close (bool): If True, the records are marked as closed after
                          recalculations are applied.

        Note:
            This method ensures that prevalence is updated for all answers
            linked to the attempt before proceeding with the calculations.
            IMPORTANT: this method does not update last_signal attribute
        """

        # Disable prevalence and rank updates within this method
        # Allow bypassing close restriction con create and write methods
        context = self.env.context.copy()
        context.update({
            'disable_prevalence_update': True,
            'disable_rank_update': True,
            'disable_attempt_update': True,
            'attempt_close_enabled': True
        })
        target_set = self.with_context(context)

        # Exclude opened attempts
        if not close:
            target_set = target_set._filter_closed_records(warning=True)

        # Update related answer prevalence
        attempt_answer_set = target_set.mapped('attempt_answer_ids')
        attempt_answer_set.update_prevalence()

        for record in target_set:
            values = record.get_computed_values()

            if close and not record.closed:
                values['closed'] = True

                record._update_time_values(values)
                record._update_values_with_missing_answers(values)
                record._log_closing()

            record.write(values)

        # See: It will be used self insted self_ctx to get global context
        if not self._ctx_disable_update('prevalence'):
            self.update_prevalence()

        # See: It will be used self insted self_ctx to get global context
        if not self._ctx_disable_update('rank'):
            self.update_rank()

        # See: It will be used self insted self_ctx to get global context
        if not self._ctx_disable_update('attempt'):
            individual_set = self.mapped('individual_id')
            individual_set.fast_update_attempt_data()

            assignment_set = self.mapped('individual_id.assignment_id')
            assignment_set.fast_update_attempt_data()

    def recalculate_all(self, close=False):
        domain = TRUE_DOMAIN if close else [('closed', '=', True)]
        attempt_obj = self.env['academy.tests.attempt']
        attempt_set = attempt_obj.search(domain)

        attempt_set.recalculate(close=close)

    def close(self):
        """
        Closes the current records by setting their status to closed and
        triggers a recalculation.

        This method acts as a shortcut to `recalculate` with the `close` flag
        set to True, ensuring all associated records are updated accordingly.
        """

        self.recalculate(close=True)

    # -------------------------------------------------------------------------
    # Update prevalence
    # -------------------------------------------------------------------------

    def _get_individual_ids(self):
        return self.mapped('individual_id').ids

    def update_prevalence(self, individual_ids=False):
        sql_pattern = '''
            WITH attempt_prevalence AS (
                SELECT
                    "id",
                    ROW_NUMBER ( ) OVER (
                        PARTITION BY individual_id
                        ORDER BY
                            individual_id,
                            active DESC NULLS LAST,
                            closed DESC NULLS LAST,
                            max_points DESC,
                            "end" ASC NULLS LAST
                    ) AS "prevalence"
                FROM
                    academy_tests_attempt
                WHERE
                    individual_id in ({ids})
            )
            UPDATE academy_tests_attempt AS att
                SET prevalence = ap."prevalence"
            FROM
                attempt_prevalence AS ap
            WHERE
                ap."id" = att."id";
        '''

        if individual_ids is False:
            individual_ids = self._get_individual_ids()

        if individual_ids:
            ids_str = ', '.join([str(item_id) for item_id in individual_ids])
            sql = sql_pattern.format(ids=ids_str)

            self._execute_query(sql, action='update_prevalence')

    @api.model
    def _execute_query(self, sql, selection=False, notify=False, action=None):
        results = []
        action = action or 'SQL'

        for attempt in range(MAX_RETRIES):
            try:
                cursor = self.env.cr
                cursor.execute(sql)

                if selection:
                    results = cursor.dictfetchall()

                break

            except SerializationFailure:
                if attempt < MAX_RETRIES - 1:
                    message = 'Failed to execute SQL {} / {} tries'
                    _logger.warning(message.format(attempt, MAX_RETRIES))
                    sleep(1)  # Wait before retry
                else:
                    if notify:
                        message = _('Failed to execute {} after {} tries')
                        raise UserError(message.format(action, MAX_RETRIES))
                    else:
                        message = 'Failed to execute {} after {} tries'
                        _logger.error(message.format(action, MAX_RETRIES))

            except Exception as ex:
                if notify:
                    message = _('Failed to execute {}. System says: {}')
                    raise UserError(message.format(action, ex))
                else:
                    message = 'Failed to execute {}. System says: {}'
                    _logger.error(message.format(action, ex))

                break

        return results if selection else True

    # -------------------------------------------------------------------------
    # Update rank
    # -------------------------------------------------------------------------

    def _get_assignment_ids(self):
        return self.mapped('assignment_id').ids

    def update_rank(self, assignment_ids=False):
        sql_pattern = '''
            WITH attempt_rank AS (
                SELECT
                    "id",
                    ROW_NUMBER ( ) OVER (
                        PARTITION BY assignment_id
                        ORDER BY
                            assignment_id,
                            active DESC NULLS LAST,
                            closed DESC NULLS LAST,
                            max_points DESC,
                            "end" ASC NULLS LAST
                    ) AS "rank"
                FROM
                    academy_tests_attempt
                WHERE
                    assignment_id in ({ids})
            )
            UPDATE academy_tests_attempt AS att
                SET rank = ap.rank
            FROM
                attempt_rank AS ap
            WHERE
                ap."id" = att."id";
        '''

        if assignment_ids is False:
            assignment_ids = self._get_assignment_ids()

        if assignment_ids:
            ids_str = ', '.join([str(item_id) for item_id in assignment_ids])
            sql = sql_pattern.format(ids=ids_str)

            self._execute_query(sql, action='update_rank')

    # -------------------------------------------------------------------------
    # Actions and Events
    # -------------------------------------------------------------------------

    def close_old_attempts(self):
        """
        Closes test attempts that are older than their configured lifespan.

        It is designed to be called by an `ir.cron` job in Odoo, automating the
        process of closing outdated attempts.
        """
        attempt_obj = self.env['academy.tests.attempt']

        life_span = self.get_attempt_lifespan()
        limit_date = fields.Datetime.now() - timedelta(days=life_span)
        domain = [('closed', '!=', True), ('start', '<=', limit_date)]
        opened_set = attempt_obj.search(domain)
        opened_set.close()

    def view_attempt_answers(self):
        self.ensure_one()

        action_xid = 'academy_tests.action_test_attempt_answers_act_window'
        act_wnd = self.env.ref(action_xid)

        name = _('Answers')

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))
        context.update({'default_attempt_id': self.id})

        domain = [('attempt_id', '=', self.id)]

        serialized = {
            'type': 'ir.actions.act_window',
            'res_model': act_wnd.res_model,
            'target': 'current',
            'name': name,
            'view_mode': act_wnd.view_mode,
            'domain': domain,
            'context': context,
            'search_view_id': act_wnd.search_view_id.id,
            'help': act_wnd.help
        }

        return serialized

    # -------------------------------------------------------------------------
    # Methods Related to res.config.settings
    # -------------------------------------------------------------------------

    @api.model
    def reconcile_all(self):
        """
        Recalculates all closed attempts and closes old attempts as defined by
        their lifespan.

        # IMPORTANT: This method is different from recalculate_all

        This function is intended to be triggered manually from a button
        located in the configuration settings (`res.config.settings`) of the
        module. It helps maintain data integrity and optimizes the performance
        of the system by managing outdated or finalized records.
        """
        self_su = self.sudo()

        domain = [('closed', '=', True)]
        attempt_obj = self_su.env['academy.tests.attempt']
        closed_set = attempt_obj.search(domain)
        closed_set.recalculate()

        # Following method closes and recalculates target records.
        # It should be called after the closed records have been recalculated
        # to avoid unnecessary repeated recomputations.
        self_su.close_old_attempts()

    def get_attempt_lifespan(self):
        """
        Retrieves the configured maximum lifespan (in days) of attempts from
        system settings. If the parameter is not set, a default value of 30
        days is used.

        Returns:
            int: The lifespan of attempts in days.

        Raises:
            ValueError, TypeError: If the parameter exists but cannot be
                                   converted to an integer, logs a warning and
                                   returns the default value.

        Usage:
            Typically called to determine how long an attempt should remain
            active before being automatically closed by (ir.cron) maintenance
            routines.
        """
        default = 30

        config_obj = self.env['ir.config_parameter'].sudo()
        param_name = 'academy_tests.attempt_lifespan'
        attempt_lifespan = config_obj.get_param(param_name, default=default)

        try:
            attempt_lifespan = int(attempt_lifespan)
        except (ValueError, TypeError) as ex:
            message = (f'Failed to convert attempt lifespan to integer. '
                       f'System says: {ex}. Using default value of 30.')
            _logger.warning(message)
            attempt_lifespan = default

        return attempt_lifespan
