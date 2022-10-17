# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from logging import getLogger


_logger = getLogger(__name__)


class AcademyPublicTenderingEvent(models.Model):
    """ Add a relationship between events and RSS items
    """

    _inherit = ['academy.public.tendering.event']

    rss_item_id = fields.Many2one(
        string='RSS Item',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Related RSS item',
        comodel_name='academy.public.tendering.rss.item',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )
