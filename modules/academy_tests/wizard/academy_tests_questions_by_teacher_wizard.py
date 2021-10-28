# -*- coding: utf-8 -*-
""" Academy Tests Question Import

This module contains the academy.tests.questions.by.teacher.wizard model
which allows to build a report which counts the number of questions by each one
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger

from enum import IntEnum
from datetime import date
from dateutil.relativedelta import relativedelta

_logger = getLogger(__name__)


class Period(IntEnum):
    TODAY = 0
    ONE_WEEK = 1
    THIS_WEEK = 2
    LAST_WEEK = 3
    ONE_MONTH = 4
    THIS_MONTH = 5
    LAST_MONTH = 6
    ONE_YEAR = 7
    THIS_YEAR = 8
    LAST_YEAR = 9


WIZARD_STATES = [
    ('step1', _('Dates')),
    ('step2', _('Teachers')),
    ('step3', _('Topics')),
]


ORDER_BY = [
    ('az', _('Name (ASC)')),
    ('za', _('Name (DESC)')),
    ('09', _('Quantity (ASC)')),
    ('90', _('Quantity (DESC)')),
]


class AcademyTestsQuestionsByTeacherWizard(models.TransientModel):
    """ Wizard to choose teacher and dates between
    """

    _name = 'academy.tests.questions.by.teacher.wizard'
    _description = u'Academy tests questions by teacher wizard'

    _rec_name = 'id'
    _order = 'id DESC'

    state = fields.Selection(
        string='State',
        required=False,
        readonly=False,
        index=False,
        default='step1',
        help='Current wizard step',
        selection=WIZARD_STATES
    )

    order_by = fields.Selection(
        string='Order by',
        required=True,
        readonly=False,
        index=False,
        default='az',
        help='Choose how records will be sorted',
        selection=ORDER_BY
    )

    teacher_ids = fields.Many2many(
        string='Teachers',
        required=False,
        readonly=False,
        index=False,
        default=lambda self: self._default_teacher_ids(),
        help=False,
        comodel_name='academy.teacher',
        relation='academy_tests_questions_by_teacher_wizard_teacher_rel',
        column1='wizard_id',
        column2='teacher_id',
        domain=[],
        context={},
        limit=None
    )

    topic_ids = fields.Many2many(
        string='Topics',
        required=False,
        readonly=False,
        index=False,
        default=lambda self: self._default_topic_ids(),
        help=False,
        comodel_name='academy.tests.topic',
        relation='academy_tests_questions_by_teacher_wizard_topic_rel',
        column1='wizard_id',
        column2='topic_id',
        domain=[],
        context={},
        limit=None
    )

    start = fields.Date(
        string='Start',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.compute_period(Period.THIS_WEEK)[0],
        help='Choose the start date'
    )

    end = fields.Date(
        string='End',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.compute_period(Period.THIS_WEEK)[1],
        help='Choose the end date'
    )

    period = fields.Selection(
        string='Period',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose period',
        selection=[
            ('0', 'Today'),
            ('1', 'One week'),
            ('2', 'This week'),
            ('3', 'Last week'),
            ('4', 'One month'),
            ('5', 'This month'),
            ('6', 'Last month'),
            ('7', 'One year'),
            ('8', 'This year'),
            ('9', 'Last year'),
        ]
    )

    allow_empty = fields.Boolean(
        string='Allow empty',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to allow empty lines'
    )

    def _default_teacher_ids(self):
        teacher_set = self.env['academy.teacher']
        active_model = self.env.context.get('active_model', False)

        if active_model == 'academy.teacher':
            active_ids = self.env.context.get('active_ids', [-1])

            teacher_domain = [('id', 'in', active_ids)]

            teacher_set = teacher_set.search(teacher_domain)

        return teacher_set

    def _default_topic_ids(self):
        teacher_set = self.teacher_ids or self._default_teacher_ids()

        question_set = self.env['academy.tests.question']

        teacher_ids = teacher_set.mapped('res_users_id.id')
        domain = [('owner_id', 'in', teacher_ids)]

        item_set = question_set.read_group(
            domain,
            fields=['topic_ids:array_agg(topic_id)'],
            groupby=['topic_id'],
            lazy=False
        )

        topic_ids = [item['topic_id'][0] for item in item_set]
        print(topic_ids)

        return [(6, 0, topic_ids)]

    @staticmethod
    def compute_period(period):
        today = date.today()

        if isinstance(period, str):
            try:
                period = eval(period)
            except Exception as ex:
                _logger.warning(ex)
                period = Period.TODAY

        if period == Period.TODAY:
            return today, today

        if period == Period.ONE_WEEK:
            start = today + relativedelta(weeks=-1, days=1)
            return start, today

        if period == Period.THIS_WEEK:
            start = today - relativedelta(days=today.weekday())
            end = today + relativedelta(days=6 - today.weekday())
            return start, end

        if period == Period.LAST_WEEK:
            start = today - relativedelta(weeks=1, days=today.weekday())
            end = today + relativedelta(weeks=-1, days=6 - today.weekday())
            return start, end

        if period == Period.ONE_MONTH:
            start = today + relativedelta(months=-1, days=1)
            return start, today

        if period == Period.THIS_MONTH:
            start = today.replace(day=1)
            end = (start + relativedelta(months=1)) - relativedelta(days=1)
            return start, end

        if period == Period.LAST_MONTH:
            start = (today - relativedelta(months=1)).replace(day=1)
            end = (start + relativedelta(months=1)) - relativedelta(days=1)
            return start, end

        if period == Period.ONE_YEAR:
            start = today + relativedelta(years=-1, days=1)
            return start, today

        if period == Period.THIS_YEAR:
            start = today.replace(day=1, month=1)
            end = (start + relativedelta(years=1)) - relativedelta(days=1)
            return start, end

        if period == Period.LAST_YEAR:
            start = (today - relativedelta(years=1)).replace(day=1, month=1)
            end = (start + relativedelta(years=1)) - relativedelta(days=1)
            return start, end

    @api.onchange('period')
    def _onchange_period(self):
        if self.period:
            start, end = self.compute_period(self.period)
            self.start = start
            self.end = end

            self.period = None

    def show_pivot(self):

        teacher_ids = self.teacher_ids.mapped('res_users_id.id')
        topic_ids = self.topic_ids.mapped('id')

        domain = [
            ('owner_id', 'in', teacher_ids),
            ('topic_id', 'in', topic_ids),
            ('create_date', '>=', fields.Date.to_string(self.start)),
            ('create_date', '<=', fields.Date.to_string(self.end)),
        ]

        print(domain)

        return {
            'model': 'ir.actions.act_window',
            'type': 'ir.actions.act_window',
            'name': _('Questions by teacher'),
            'res_model': 'academy.tests.question',
            'view_mode': 'pivot',
            'target': 'current',
            'domain': domain,
            'context': {
                'group_by': ['owner_id', 'topic_id']
            }
        }
