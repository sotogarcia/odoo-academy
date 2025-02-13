# -*- coding: utf-8 -*-
""" AcademyTestsAttempt

This module contains the academy.tests.attempt Odoo model which stores
all academy tests attempt attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from .utils.sql_inverse_searches import ATTEMPTS_CLOSED_SEARCH
from odoo.osv.expression import FALSE_DOMAIN, TRUE_DOMAIN

from logging import getLogger
from datetime import datetime

_logger = getLogger(__name__)


class AcademyAbstractAttempt(models.AbstractModel):
    """ Logs an attempt by a user to solve a test
    """

    _name = 'academy.abstract.attempt'
    _description = u'Academy abstract attempt'

    _rec_name = 'id'
    _order = 'start DESC'

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this attempt',
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Check it to show this attempt or uncheck to archivate'
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

    assignment_id = fields.Many2one(
        string='Training assignment',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.test.training.assignment',
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
        digits=(16, 10),
        help='Enter the time has been used in attempt'
    )

    available_time = fields.Float(
        string='Available time',
        required=True,
        readonly=False,
        index=False,
        default=0.0,
        digits=(8, 6),
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
        string='Time by',
        required=True,
        readonly=False,
        index=False,
        default='test',
        help='Choose how the total time is calculated',
        selection=[('question', 'By question'), ('test', 'By test')]
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

    attempt_final_answer_ids = fields.Many2manyView(
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
                record.elapsed = min(record.available_time, elapsed)

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

    enrolment_id = fields.Many2one(
        string='Enrolment',
        related='assignment_id.enrolment_id'
    )

    training_action_id = fields.Many2one(
        string='Training action',
        related='assignment_id.training_action_id'
    )

    training_activity_id = fields.Many2one(
        string='Training activity',
        related='assignment_id.training_activity_id'
    )

    competency_unit_id = fields.Many2one(
        string='Competency unit',
        related='assignment_id.competency_unit_id'
    )

    training_module_id = fields.Many2one(
        string='Training module',
        related='assignment_id.training_module_id'
    )

    topic_ids = fields.Many2many(
        string='Topics',
        readonly=True,
        help='Topics from all the questions in the attempt',
        related='assignment_id.test_id.topic_ids'
    )

    tag_ids = fields.Many2many(
        string='Tags',
        readonly=True,
        help='Tag can be used to better describe this question',
        related='assignment_id.test_id.tag_ids'
    )
