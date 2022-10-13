# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from logging import getLogger

from odoo.tools import drop_view_if_exists
from .utils.view_academy_tests_question_statistics_helper import \
    VIEW_ACADEMY_TESTS_QUESTION_STATISTICS_HELPER

_logger = getLogger(__name__)


class AcademyTestsQuestionStudentStatisticsHelper(models.Model):
    """ Question statistics by enrolment
    """

    _inherit = ['academy.tests.abstract.question.statistics']

    _name = 'academy.tests.question.student.statistics.helper'
    _description = u'Academy tests question student statistics helper'

    _rec_name = 'id'
    _order = 'id DESC'

    _auto = False

    _groupby = 'tae."student_id"'
    _related = 'student_id'

    student_id = fields.Many2one(
        string='Student',
        required=True,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.student',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )
