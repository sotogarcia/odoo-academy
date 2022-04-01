# -*- coding: utf-8 -*-
""" AcademyCompetencyUnit

This module extends the academy.competency.unit Odoo model
"""

from odoo import models, fields

import odoo.addons.academy_base.models.utils.custom_model_fields as custom
from .utils.sql_m2m_through_view import \
    ACADEMY_TESTS_TEST_AVAILABLE_IN_COMPETENCY_UNIT_REL

from logging import getLogger

_logger = getLogger(__name__)


class AcademyCompetencyUnit(models.Model):
    """ Extends model adding two many2many fields to link tests and units
    """

    _inherit = 'academy.competency.unit'

    competency_test_ids = fields.Many2many(
        string='Competency unit tests',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose the tests will be available in this competency unit',
        comodel_name='academy.tests.test',
        relation='academy_tests_test_competency_unit_rel',
        column1='competency_unit_id',
        column2='test_id',
        domain=[],
        context={},
        limit=None
    )

    competency_available_test_ids = custom.Many2manyThroughView(
        string='Competency unit available tests',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose the tests will be available in this competency unit',
        comodel_name='academy.tests.test',
        relation='academy_tests_test_available_in_competency_unit_rel',
        column1='competency_unit_id',
        column2='test_id',
        domain=[],
        context={},
        limit=None,
        sql=ACADEMY_TESTS_TEST_AVAILABLE_IN_COMPETENCY_UNIT_REL
    )

    def create_test_template(self, no_open=False):
        template_obj = self.env['academy.tests.random.template']
        module_obj = self.env['academy.training.module']

        values = module_obj.get_template_values(self)

        template = template_obj.create(values)

        if not no_open and template:
            return module_obj._template_act_window(template)
