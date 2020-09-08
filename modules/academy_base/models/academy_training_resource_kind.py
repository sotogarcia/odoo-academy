# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingResourceKind(models.Model):
    """ Kind for academy training resource
    """

    _name = 'academy.training.resource.kind'
    _description = u'Academy training resource kind'

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

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Enter new description',
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Enables/disables the record'
    )

    resource_ids = fields.One2many(
        string='Tests',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.resource',
        inverse_name='kind_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )
