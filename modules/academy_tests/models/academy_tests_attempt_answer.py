# -*- coding: utf-8 -*-
""" AcademyTestsAttemptAnswer

This module contains the academy.tests.attempt.answer Odoo model which stores
all academy tests attempt answer attributes and behavior.
"""

from odoo import models
from logging import getLogger

_logger = getLogger(__name__)


class AcademyTestAttemptAnswer(models.Model):
    """ Logs all student answers in a test attempt, even if later he
    change it by another answer
    """

    _name = 'academy.tests.attempt.answer'
    _description = u'Academy tests attempt answer'

    _inherit = ['academy.abstract.attempt.answer']

    _rec_name = 'id'
    _order = 'instant DESC'
