# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger
from odoo.addons.academy_base.models.lib.custom_model_fields import Many2manyThroughView
from .lib.libuseful import ACADEMY_COMPETENCY_AVAILABLE_TESTS


_logger = getLogger(__name__)


class AcademyCompetencyUnit(models.Model):
    """ Extends model adding a many2many field to link tests to units
    """

    _inherit = 'academy.competency.unit'

    competency_test_ids = fields.Many2many(
        string='Tests',
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

    competency_available_test_ids = Many2manyThroughView(
        string='Tests',
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
        sql=ACADEMY_COMPETENCY_AVAILABLE_TESTS
    )
