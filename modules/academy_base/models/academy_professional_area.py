# -*- coding: utf-8 -*-
""" AcademyTrainingAction

This module contains the academy.professional.area Odoo model which stores
all professional area attributes and behavior.
"""


from logging import getLogger

# pylint: disable=locally-disabled, E0401
from odoo import models, fields


# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyProfessionalArea(models.Model):
    """ ...

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.professional.area'
    _description = u'Academy professional area'

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

    professional_qualification_ids = fields.One2many(
        string='Professional qualifications',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.professional.qualification',
        inverse_name='professional_area_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )


