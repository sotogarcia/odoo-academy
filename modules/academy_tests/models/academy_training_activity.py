# -*- coding: utf-8 -*-
""" AcademyTrainingActivity

This module extends the academy.training.activity Odoo model
"""

from odoo import models, fields

import odoo.addons.academy_base.models.utils.custom_model_fields as custom
from .utils.sql_m2m_through_view import ACADEMY_ACTIVITY_AVAILABLE_TESTS, \
    PARTIAL_ACADEMY_TESTS_QUESTION_TRAINING_MODULE, \
    ACADEMY_TESTS_QUESTION_TRAINING_ACTIVITY_REL

from logging import getLogger

_logger = getLogger(__name__)

AVAILABLE_QUESTIONS = ACADEMY_TESTS_QUESTION_TRAINING_ACTIVITY_REL.format(
    PARTIAL_ACADEMY_TESTS_QUESTION_TRAINING_MODULE)


class AcademyTrainingActivity(models.Model):
    """ Extends model adding a many2many field to link tests to actions
    """

    _inherit = 'academy.training.activity'

    test_ids = fields.Many2many(
        string='Activity tests',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose the tests will be available in this training activity',
        comodel_name='academy.tests.test',
        relation='academy_tests_test_training_activity_rel',
        column1='training_activity_id',
        column2='test_id',
        domain=[],
        context={},
        limit=None
    )

    available_test_ids = custom.Many2manyThroughView(
        string='Activity available tests',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose the tests will be available in this training activity',
        comodel_name='academy.tests.test',
        relation='academy_tests_test_available_in_training_activity_rel',
        column1='training_activity_id',
        column2='test_id',
        domain=[],
        context={},
        limit=None,
        sql=ACADEMY_ACTIVITY_AVAILABLE_TESTS
    )

    template_link_ids = fields.Many2many(
        string='Random templates',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose random template',
        comodel_name='academy.tests.random.template',
        relation='academy_tests_random_template_training_activity_rel',
        column1='training_activity_id',
        column2='random_template_id',
        domain=[],
        context={},
        limit=None
    )

    available_question_ids = custom.Many2manyThroughView(
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
