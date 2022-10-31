# -*- coding: utf-8 -*-
""" AcademyTrainingModule

This module extends the academy.training.module Odoo model
"""

from odoo import models, fields, api
from odoo.tools.translate import _

from .utils.sql_m2m_through_view import INHERITED_TOPICS_REL
from .utils.sql_m2m_through_view import INHERITED_CATEGORIES_REL
from .utils.sql_m2m_through_view import \
    PARTIAL_ACADEMY_TESTS_QUESTION_TRAINING_MODULE
from .utils.sql_m2m_through_view import \
    ACADEMY_TESTS_QUESTION_TRAINING_MODULE_REL

from logging import getLogger
from datetime import datetime
import re

_logger = getLogger(__name__)

AVAILABLE_QUESTIONS = ACADEMY_TESTS_QUESTION_TRAINING_MODULE_REL.format(
    PARTIAL_ACADEMY_TESTS_QUESTION_TRAINING_MODULE)


class AcademyTrainingModule(models.Model):
    """ Extends academy.training.module to link to training topic
    """

    _name = 'academy.training.module'
    _inherit = ['academy.training.module']

    assignment_ids = fields.One2many(
        string='Test assignments',
        required=False,
        readonly=False,
        index=True,
        default=None,
        comodel_name='academy.tests.test.training.assignment',
        inverse_name='training_module_id',
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

    topic_link_ids = fields.One2many(
        string='Topics',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Link test topics to this module',
        comodel_name='academy.tests.topic.training.module.link',
        inverse_name='training_module_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None,
    )

    available_topic_ids = fields.Many2manyThroughView(
        string='Available topics',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.topic',
        relation='academy_training_module_test_topic_rel',
        column1='training_module_id',
        column2='test_topic_id',
        domain=[],
        context={},
        limit=None,
        sql=INHERITED_TOPICS_REL
    )

    available_categories_ids = fields.Many2manyThroughView(
        string='Available categories',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.category',
        relation='academy_training_module_test_category_rel',
        column1='training_module_id',
        column2='test_category_id',
        domain=[],
        context={},
        limit=None,
        sql=INHERITED_CATEGORIES_REL
    )

    available_question_ids = fields.Many2manyThroughView(
        string='Available questions',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Show questions available in the module',
        comodel_name='academy.tests.question',
        relation='academy_tests_question_training_module_rel',
        column1='training_module_id',
        column2='question_id',
        domain=[],
        context={},
        limit=None,
        sql=AVAILABLE_QUESTIONS
    )

    @staticmethod
    def _template_name(target_set, name):
        if not name:
            if len(target_set) == 1:
                name = getattr(target_set, 'competency_name', target_set.name)
            else:
                now_str = datetime.now().strftime('%Y-%m-%d_-_%H-%M-%S')
                name = _('Template {}').format(now_str)

        return name

    def _line_default_question_type(self):
        theoretical_id = None

        try:
            theoretical_xid = 'academy_tests.academy_tests_question_type_1'
            theoretical_id = self.env.ref(theoretical_xid).id
        except Exception as ex:
            _logger.debug(ex)

        return theoretical_id

    @staticmethod
    def _append_context(values, context):

        if context and len(context) == 1:
            pattern = r'([^(]+)\(([^,]+),\)'
            replacement = r'\1,\2'

            value = re.sub(pattern, replacement, str(context))

            values['training_ref'] = value
