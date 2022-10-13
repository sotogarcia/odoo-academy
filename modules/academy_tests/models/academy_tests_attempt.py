# -*- coding: utf-8 -*-
""" AcademyTestsAttemptAnswer

This module contains the academy.tests.attempt.answer Odoo model which stores
all academy tests attempt answer attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger

_logger = getLogger(__name__)


class AcademyTestAttempt(models.Model):
    """ Logs all student answers in a test attempt, even if later he
    change it by another answer
    """

    _name = 'academy.tests.attempt'
    _description = u'Academy tests attempt'

    _inherit = ['academy.abstract.attempt']

    _rec_name = 'id'
    _order = 'start DESC'

    test_id = fields.Many2one(
        string='Test',
        readonly=True,
        related="assignment_id.test_id"
    )
