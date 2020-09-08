# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger
from odoo.addons.academy_base.models.lib.custom_model_fields import Many2manyThroughView
from .lib.libuseful import ACADEMY_STUDENT_AVAILABLE_TESTS

_logger = getLogger(__name__)


class AcademyStudent(models.Model):
    """ Extend student adding available tests
    """

    _inherit = 'academy.student'

    available_test_ids = Many2manyThroughView(
        string='Tests',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose the tests will be available to this student',
        comodel_name='academy.tests.test',
        relation='academy_tests_test_available_in_student_rel',
        column1='student_id',
        column2='test_id',
        domain=[],
        context={},
        limit=None,
        sql=ACADEMY_STUDENT_AVAILABLE_TESTS
    )
