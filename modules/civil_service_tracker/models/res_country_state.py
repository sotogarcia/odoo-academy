# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class ResCountryState(models.Model):

    _name = 'res.country.state'
    _inherit = ['res.country.state']

    administrative_region_id = fields.Many2one(
        string='Administrative region',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help=False,
        comodel_name='civil.service.tracker.administrative.region',
        domain=[],
        context={},
        ondelete='set null',
        auto_join=False
    )
