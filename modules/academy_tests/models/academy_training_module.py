# -*- coding: utf-8 -*-
""" AcademyTrainingModule

This module extends the academy.training.module Odoo model
"""

from odoo import models, fields
from odoo.tools.translate import _

import odoo.addons.academy_base.models.utils.custom_model_fields as custom
from .utils.sql_m2m_through_view import INHERITED_TOPICS_REL, \
    INHERITED_CATEGORIES_REL, ACADEMY_MODULE_AVAILABLE_TESTS, \
    PARTIAL_ACADEMY_TESTS_QUESTION_TRAINING_MODULE, \
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

    available_topic_ids = custom.Many2manyThroughView(
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

    available_categories_ids = custom.Many2manyThroughView(
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

    test_ids = fields.Many2many(
        string='Training module tests',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose the tests related with this training module',
        comodel_name='academy.tests.test',
        relation='academy_tests_test_training_module_rel',
        column1='training_module_id',
        column2='test_id',
        domain=[],
        context={},
        limit=None
    )

    available_test_ids = custom.Many2manyThroughView(
        string='Training module available tests',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose the tests will be available in this training module',
        comodel_name='academy.tests.test',
        relation='academy_tests_test_available_in_training_module_rel',
        column1='training_module_id',
        column2='test_id',
        domain=[],
        context={},
        limit=None,
        sql=ACADEMY_MODULE_AVAILABLE_TESTS
    )

    template_link_ids = fields.Many2many(
        string='Random templates',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose random template',
        comodel_name='academy.tests.random.template',
        relation='academy_tests_random_template_training_module_rel',
        column1='training_module_id',
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
            print(value)

            values['context_ref'] = value

    @staticmethod
    def _template_act_window(template):

        if not template:
            return False

        return {
            'name': template.name,
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'academy.tests.random.template',
            'res_id': template.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
        }

    def get_template_values(self, target_set, name=None, context=None):

        template_values = dict(
            name=self._template_name(target_set, name),
            description=None,
            active=True,
            random_line_ids=[(5, None, None)],
        )

        self._append_context(template_values, context)

        line_sequence = 0
        question_type_id = self._line_default_question_type()

        for record in target_set:

            line_name = getattr(record, 'competency_name', record.name)

            line_sequence += 10
            line_values = dict(
                random_template_id='',
                name=line_name,
                description=None,
                active=True,
                sequence=line_sequence,
                quantity=2,
                type_ids=[(6, 0, [question_type_id])],
                authorship='own',
                exclude_tests=True,
                tests_by_context=True,
                categorization_ids=[(5, None, None)],
                stock=1.00,
                stock_by='pct'
            )

            categorization_sequence = 0
            for link in record.topic_link_ids:
                category_ids = link.mapped('category_ids.id')

                categorization_sequence += 10
                categorizacion_values = dict(
                    description=link.topic_id.name,
                    active=True,
                    sequence=categorization_sequence,
                    topic_id=link.topic_id.id,
                    topic_version_ids=[(6, None, [link.topic_version_id.id])],
                    category_ids=[(6, None, category_ids)],
                )

                m2m_categorization = (0, 0, categorizacion_values)
                line_values['categorization_ids'].append(m2m_categorization)

            m2m_line = (0, 0, line_values)
            template_values['random_line_ids'].append(m2m_line)

        return template_values

    def create_test_template(self, no_open=False):
        template_obj = self.env['academy.tests.random.template']

        values = self.get_template_values(self)

        template = template_obj.create(values)

        if not no_open and template:
            return self._template_act_window(template)
