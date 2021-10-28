# -*- coding: utf-8 -*-
""" AcademyQualificationLevel

This module contains the academy.qualification.level Odoo model which stores
all qualification level attributes and behavior.
"""

from odoo import models, fields

from logging import getLogger

_logger = getLogger(__name__)


class AcademyQualificationLevel(models.Model):
    """ Qualification level is a property of the training activity
    """

    _name = 'academy.qualification.level'
    _description = u'Academy qualification level'

    _rec_name = 'name'
    _order = 'sequence ASC, name ASC'

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

    level = fields.Char(
        string='Code',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Enter new code',
        size=8,
        translate=True
    )

    sequence = fields.Integer(
        string='Sequence',
        required=True,
        readonly=False,
        index=False,
        default=0,
        help='Choose level order'
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Enables/disables the record'
    )
