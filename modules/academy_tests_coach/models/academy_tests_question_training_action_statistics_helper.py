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


class AcademyTestsQuestionTrainingActionStatisticsHelper(models.Model):
    """ Question statistics by training action
    """

    _inherit = ['academy.tests.abstract.question.statistics']

    _name = 'academy.tests.question.training.action.statistics.helper'
    _description = u'Academy tests question trainin action statistics helper'

    _rec_name = 'id'
    _order = 'id DESC'

    _auto = False

    _groupby = 'tae.training_action_id'
    _related = 'training_action_id'

    training_action_id = fields.Many2one(
        string='Trainin action',
        required=True,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.action',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )
