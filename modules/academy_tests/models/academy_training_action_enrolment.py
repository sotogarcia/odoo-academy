# -*- coding: utf-8 -*-
""" AcademyTrainingActionEnrolment

This module extends the academy.training.action.enrolment Odoo model
"""

from odoo import models, fields

import odoo.addons.academy_base.models.utils.custom_model_fields as custom
from .utils.sql_m2m_through_view import ACADEMY_ENROLMENT_AVAILABLE_TESTS

from logging import getLogger

_logger = getLogger(__name__)

LONG_NAME = 'academy_tests_test_available_in_training_action_enrolment_rel'


class AcademyTrainingActionEnrolment(models.Model):
    """ Extends model adding a many2many field to link tests to actions
    """

    _inherit = 'academy.training.action.enrolment'

    test_ids = fields.Many2many(
        string='Entolment tests',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=('Choose the tests will be available in this training action '
              'enrolment'),
        comodel_name='academy.tests.test',
        relation='academy_tests_test_training_action_enrolment_rel',
        column1='enrolment_id',
        column2='test_id',
        domain=[],
        context={},
        limit=None
    )

    available_test_ids = custom.Many2manyThroughView(
        string='Enrolment available tests',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose the tests will be available in this training activity',
        comodel_name='academy.tests.test',
        relation=LONG_NAME,
        column1='enrolment_id',
        column2='test_id',
        domain=[],
        context={},
        limit=None,
        sql=ACADEMY_ENROLMENT_AVAILABLE_TESTS
    )
