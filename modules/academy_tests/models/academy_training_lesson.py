# -*- coding: utf-8 -*-
""" AcademyTrainingLesson

This module extends the academy.training.lesson Odoo model
"""

from odoo import models, fields

from logging import getLogger

_logger = getLogger(__name__)


class AcademyTrainingLesson(models.Model):
    """ Extends model adding a many2many field to link tests to actions
    """

    _inherit = 'academy.training.lesson'

    test_ids = fields.Many2many(
        string='Lesson tests',
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
