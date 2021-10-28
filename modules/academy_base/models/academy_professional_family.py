# -*- coding: utf-8 -*-
""" AcademyProfessionalFamily

This module contains the academy.professional.family Odoo model which stores
all professional family attributes and behavior.
"""

from odoo import models, fields, api

from logging import getLogger

_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyProfessionalFamily(models.Model):
    """ Professional family is a property of the training activity
    """

    _name = 'academy.professional.family'
    _description = u'Academy professional family'

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

    professional_area_ids = fields.One2many(
        string='Professional area',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.professional.area',
        inverse_name='professional_family_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    professional_qualification_ids = fields.One2many(
        string='Professional qualifications',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.professional.qualification',
        inverse_name='professional_family_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    # -------------------------- MANAGEMENT FIELDS ----------------------------

    # pylint: disable=locally-disabled, W0212
    professional_area_count = fields.Integer(
        string='Professional areas',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help=('Shows the number of professional areas that belong to this '
              'family'),
        compute=lambda self: self._compute_professional_area_count()
    )

    @api.depends('professional_area_ids')
    def _compute_professional_area_count(self):
        for record in self:
            record.professional_area_count = len(record.professional_area_ids)
