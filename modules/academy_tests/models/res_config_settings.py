# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from logging import getLogger


_logger = getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    """ Module configuration attributes
    """

    _inherit = ['res.config.settings']

    categorize_from_last_questions = fields.Integer(
        string='Questions',
        required=False,
        readonly=False,
        index=False,
        default=3,
        help=('Number of questions will be used to compute categorization to '
              'apply as default in new created questions'),
        config_parameter="academy_tests.categorize_from_last_questions",
    )

    autocategorization_flags = fields.Integer(
        string='Autocategorization',
        required=False,
        readonly=False,
        index=False,
        default=7,
        help='Determines how the autocategorization function will behave'
    )
