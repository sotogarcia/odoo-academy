# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingLesson(models.Model):
    """ Extends model adding a many2many field to link tests to actions
    """

    _inherit = 'academy.training.lesson'


    test_ids = fields.Many2many(
        string='Tests',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose the tests will be available in this training action',
        comodel_name='academy.tests.test',
        relation='academy_tests_test_training_lesson_rel',
        column1='lesson_id',
        column2='test_id',
        domain=[],
        context={},
        limit=None
    )

