# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.addons.academy_base.models.lib.custom_model_fields import Many2manyThroughView
from .lib.libuseful import INHERITED_TOPICS_REL, INHERITED_CATEGORIES_REL, \
    ACADEMY_MODULE_AVAILABLE_TESTS

from logging import getLogger


_logger = getLogger(__name__)



class AcademyTrainingModule(models.Model):
    """ Extends academy.training.module to link to training topic

    Fields:
      topic_ids (One2many): Test topics linked to the module record.

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

    available_topic_ids = Many2manyThroughView(
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

    available_categories_ids = Many2manyThroughView(
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
        string='Tests',
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

    available_test_ids = Many2manyThroughView(
        string='Tests',
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
