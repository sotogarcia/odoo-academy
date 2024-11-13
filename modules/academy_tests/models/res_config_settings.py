# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _

from logging import getLogger


_logger = getLogger(__name__)

CORRECTION_SCALE_XID = 'academy_tests.academy_tests_correction_scale_default'


class ResConfigSettings(models.TransientModel):
    ''' Module configuration attributes
    '''

    _inherit = ['res.config.settings']

    correction_scale_id = fields.Many2one(
        string='Correction scale',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.env.ref(CORRECTION_SCALE_XID),
        help='The default correction scale to be used for attempts',
        comodel_name='academy.tests.correction.scale',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        config_parameter='academy_tests.correction_scale_id'
    )

    attempt_lifespan = fields.Integer(
        string='Attempt lifespan (days) ',
        required=True,
        readonly=False,
        index=False,
        default=30,
        help=False,
        config_parameter='academy_tests.attempt_lifespan'
    )
