# -*- coding: utf-8 -*-
""" AcademyCompetencyUnit

This module extends the academy.student Odoo model
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.osv.expression import FALSE_DOMAIN
from .utils.sql_inverse_searches import SEARCH_STUDENT_ATTEMPT_COUNT

from logging import getLogger

_logger = getLogger(__name__)


class AcademyStudent(models.Model):
    """ Extend student adding available tests
    """

    _inherit = 'academy.student'


