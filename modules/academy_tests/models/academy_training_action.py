# -*- coding: utf-8 -*-
""" AcademyTrainingAction

This module extends the academy.training.action Odoo model
"""

from odoo import models, fields

import odoo.addons.academy_base.models.utils.custom_model_fields as custom
from .utils.sql_m2m_through_view import ACADEMY_ACTION_AVAILABLE_TESTS

from logging import getLogger
_logger = getLogger(__name__)


class AcademyTrainingAction(models.Model):
    """ Extends model adding a many2many field to link tests to actions
    """

    _inherit = 'academy.training.action'

    test_ids = fields.Many2many(
        string='Training action tests',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose the tests will be available in this training action',
        comodel_name='academy.tests.test',
        relation='academy_tests_test_training_action_rel',
        column1='training_action_id',
        column2='test_id',
        domain=[],
        context={},
        limit=None
    )

    available_test_ids = custom.Many2manyThroughView(
        string='Training action available tests',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose the tests will be available in this training activity',
        comodel_name='academy.tests.test',
        relation='academy_tests_test_available_in_training_action_rel',
        column1='training_action_id',
        column2='test_id',
        domain=[],
        context={},
        limit=None,
        sql=ACADEMY_ACTION_AVAILABLE_TESTS
    )
