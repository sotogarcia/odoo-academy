# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from openerp import models, fields, api, api
from openerp.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class AcademyProfessionalArea(models.Model):
    """ ...

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.professional.area'
    _description = u'Academy professional area'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Enter new name',
        size=100,
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
        default='Enables/disables the record',
        help=False
    )

    professional_family_id = fields.Many2one(
        string='Professional family',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose professional family to which this area belongs',
        comodel_name='academy.professional.family',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )
