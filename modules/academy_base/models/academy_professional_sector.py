# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class AcademyProfessionalSector(models.Model):
    """ Academy professional sector
    """

    _name = 'academy.professional.sector'
    _description = u'Academy professional sector'

    _inherit = ['image.mixin']

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Enter new name',
        size=255,
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

    code = fields.Char(
        string='Code',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Enter new code',
        size=8,
        translate=True
    )

    professional_field_id = fields.Many2one(
        string='Professional field',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose related professional field',
        comodel_name='academy.professional.field',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )
