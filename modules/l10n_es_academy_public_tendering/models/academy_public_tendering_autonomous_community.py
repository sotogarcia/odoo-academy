# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class AcademyPublicTenderingAutonomousCommunity(models.Model):
    """ The summary line for a class docstring should fit on one line.

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.public.tendering.autonomous.community'
    _description = u'Academy public tendering autonomous community'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=False,
        size=50,
        translate=True
    )


    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Check it to show this attempt or uncheck to archivate'
    )

    res_country_state_ids = fields.One2many(
        string='States',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose states belongs to this autonomous community',
        comodel_name='res.country.state',
        inverse_name='autonomy_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )
