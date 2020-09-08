# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger
from odoo.addons.academy_base.models.lib.custom_model_fields import Many2manyThroughView
from .lib.libuseful import ACADEMY_ACTIVITY_AVAILABLE_TESTS

_logger = getLogger(__name__)


class AcademyTrainingActivity(models.Model):
    """ Extends model adding a many2many field to link tests to actions
    """

    _inherit = 'academy.training.activity'


    test_ids = fields.Many2many(
        string='Tests',
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

    available_test_ids = Many2manyThroughView(
        string='Tests',
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
