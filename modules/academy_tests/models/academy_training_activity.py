# -*- coding: utf-8 -*-
""" AcademyTrainingActivity

This module extends the academy.training.activity Odoo model
"""

from odoo import models, fields, api

from .utils.sql_m2m_through_view import \
    PARTIAL_ACADEMY_TESTS_QUESTION_TRAINING_MODULE
from .utils.sql_m2m_through_view import \
    ACADEMY_TESTS_QUESTION_TRAINING_ACTIVITY_REL

from odoo.tools.translate import _
from logging import getLogger

_logger = getLogger(__name__)

AVAILABLE_QUESTIONS = ACADEMY_TESTS_QUESTION_TRAINING_ACTIVITY_REL.format(
    PARTIAL_ACADEMY_TESTS_QUESTION_TRAINING_MODULE)


class AcademyTrainingActivity(models.Model):
    """ Extends model adding a many2many field to link tests to actions
    """

    _inherit = 'academy.training.activity'

    assignment_ids = fields.One2many(
        string='Test assignments',
        required=False,
        readonly=False,
        index=True,
        default=None,
        comodel_name='academy.tests.test.training.assignment',
        inverse_name='training_activity_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None,
        help=('List of test assignments that have been created for this '
              'training action enrollment')
    )

    assignment_count = fields.Integer(
        string='Nº assignments',
        required=False,
        readonly=True,
        index=False,
        default=0,
        store=False,
        compute='_compute_assignment_count',
        help=('Show the number of test assignments that have been created for'
              'this training action enrollment')
    )

    @api.depends('assignment_ids')
    def _compute_assignment_count(self):
        for record in self:
            record.assignment_count = \
                len(record.assignment_ids)

    available_question_ids = fields.Many2manyThroughView(
        string='Available questions',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Show questions available in the module',
        comodel_name='academy.tests.question',
        relation='academy_tests_question_training_activity_rel',
        column1='training_activity_id',
        column2='question_id',
        domain=[],
        context={},
        limit=None,
        sql=AVAILABLE_QUESTIONS
    )
