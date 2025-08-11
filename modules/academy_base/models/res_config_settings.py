# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _

from logging import getLogger


_logger = getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    ''' Module configuration attributes
    '''

    _inherit = ['res.config.settings']

    head_of_studies_id = fields.Many2one(
        string='Head of studies',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.env.ref('base.user_admin'),
        help='User responsible for academic oversight within the platform.',
        comodel_name='res.users',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        config_parameter='academy_base.head_of_studies_id'
    )

    erp_manager_id = fields.Many2one(
        string='ERP Manager',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.env.ref('base.user_admin'),
        help='User responsible for functional supervision of the ERP system.',
        comodel_name='res.users',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        config_parameter='academy_base.erp_manager_id'
    )
