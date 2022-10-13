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


class AcademyTestsQuestionEnrolmentStatisticsHelper(models.Model):
    """ Question statistics by enrolment
    """

    _inherit = ['academy.tests.abstract.question.statistics']

    _name = 'academy.tests.question.enrolment.statistics.helper'
    _description = u'Academy tests question enrolment statistics helper'

    _rec_name = 'id'
    _order = 'id DESC'

    _auto = False

    _groupby = 'tae."id"'
    _related = 'enrolment_id'

    enrolment_id = fields.Many2one(
        string='Enrolment',
        required=True,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.action.enrolment',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )
