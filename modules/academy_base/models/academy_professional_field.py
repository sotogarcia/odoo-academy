# -*- coding: utf-8 -*-
""" AcademyProfessionalField

This module contains the academy.professional.field Odoo model which stores
all professional field attributes and behavior.
"""

from odoo import models, fields

from logging import getLogger

_logger = getLogger(__name__)


class AcademyProfessionalField(models.Model):
    """ Professional field is a property of the training activity
    """

    _name = 'academy.professional.field'
    _description = u'Academy professional field'

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
