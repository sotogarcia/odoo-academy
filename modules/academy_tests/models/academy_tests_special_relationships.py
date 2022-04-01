# -*- coding: utf-8 -*-
""" AcademyTestsTopic

This module contains extends some models with special relationships
"""

from odoo import models, fields
import odoo.addons.academy_base.models.utils.custom_model_fields as custom

from .utils.sql_m2m_through_view import INHERITED_TOPICS_REL, \
    ACADEMY_TRAINING_ACTIVITY_TEST_TOPIC_REL, \
    ACADEMY_COMPETENCY_UNIT_TEST_TOPIC_REL


from .utils.sql_m2m_through_view import INHERITED_CATEGORIES_REL, \
    ACADEMY_TRAINING_ACTIVITY_TEST_CATEGORY_REL, \
    ACADEMY_COMPETENCY_UNIT_TEST_CATEGORY_REL

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTestsTopicSpecial(models.Model):
    """ Extends academy.tests.topic with special relationships
    """

    _inherit = 'academy.tests.topic'

    training_activity_ids = custom.Many2many(
        string='Activities',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='List all training activities that use this topic',
        comodel_name='academy.training.activity',
        relation='academy_training_activity_test_topic_rel',
        column1='test_topic_id',
        column2='training_activity_id',
        domain=[],
        context={},
        limit=None,
        sql=ACADEMY_TRAINING_ACTIVITY_TEST_TOPIC_REL
    )

    competency_unit_ids = custom.Many2many(
        string='Competency units',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='List all competency units that use this topic',
        comodel_name='academy.competency.unit',
        relation='academy_competency_unit_test_topic_rel',
        column1='test_topic_id',
        column2='competency_unit_id',
        domain=[],
        context={},
        limit=None,
        sql=ACADEMY_COMPETENCY_UNIT_TEST_TOPIC_REL
    )

    training_module_ids = custom.Many2many(
        string='Modules',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='List all training modules that use this topic',
        comodel_name='academy.training.module',
        relation='academy_training_module_test_topic_rel',
        column1='test_topic_id',
        column2='training_module_id',
        domain=[],
        context={},
        limit=None,
        sql=INHERITED_TOPICS_REL
    )

    link_ids = fields.Many2many(
        string='Link ids',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.topic.training.module.link',
        relation='academy_training_module_link_test_topic_rel',
        column1='test_topic_id',
        column2='training_module_id',
        domain=[],
        context={},
        limit=None
    )


class AcademyTestsCategorySpecial(models.Model):
    """ Extends academy.tests.category with special relationships
    """

    _inherit = 'academy.tests.category'

    training_activity_ids = custom.Many2many(
        string='Activities',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='List all training activities that use this category',
        comodel_name='academy.training.activity',
        relation='academy_training_activity_test_category_rel',
        column1='test_category_id',
        column2='training_activity_id',
        domain=[],
        context={},
        limit=None,
        sql=ACADEMY_TRAINING_ACTIVITY_TEST_CATEGORY_REL
    )

    competency_unit_ids = custom.Many2many(
        string='Competency units',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='List all competency units that use this category',
        comodel_name='academy.competency.unit',
        relation='academy_competency_unit_test_category_rel',
        column1='test_category_id',
        column2='competency_unit_id',
        domain=[],
        context={},
        limit=None,
        sql=ACADEMY_COMPETENCY_UNIT_TEST_CATEGORY_REL
    )

    training_module_ids = custom.Many2many(
        string='Modules',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='List all training modules that use this category',
        comodel_name='academy.training.module',
        relation='academy_training_module_test_category_rel',
        column1='test_category_id',
        column2='training_module_id',
        domain=[],
        context={},
        limit=None,
        sql=INHERITED_CATEGORIES_REL
    )

    link_ids = fields.Many2many(
        string='Link ids',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.topic.training.module.link',
        relation='academy_training_module_link_test_category_rel',
        column1='test_topic_id',
        column2='training_module_id',
        domain=[],
        context={},
        limit=None
    )
