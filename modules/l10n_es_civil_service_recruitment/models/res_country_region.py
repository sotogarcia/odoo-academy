# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class ResCountryRegon(models.Model):
    """ Intended for use primarily with the spanish autonomous community
    """

    _name = 'res.country.region'
    _description = u'Country region'

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

    state_ids = fields.One2many(
        string='States',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose states belongs to this autonomous community',
        comodel_name='res.country.state',
        inverse_name='region_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )
