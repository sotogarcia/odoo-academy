# -*- coding: utf-8 -*-
""" AcademyProfessionalCategory

This module contains the academy.professional.category Odoo model which stores
all Professional Area attributes and behavior.
"""

from odoo import models, fields

from logging import getLogger

_logger = getLogger(__name__)


class AcademyProfessionalCategory(models.Model):
    """Professional category is a property of the training action"""

    _name = "academy.professional.category"
    _description = "Academy professional category"

    _rec_name = "name"
    _order = "name ASC"

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Official name of the Professional Category",
        size=255,
        translate=True,
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Detailed description of the Professional Category",
        translate=True,
    )

    active = fields.Boolean(
        string="Active",
        required=False,
        readonly=False,
        index=False,
        default=True,
        help="Disable to archive without deleting.",
    )

    sequence = fields.Integer(
        string="Sequence",
        required=True,
        readonly=False,
        index=False,
        default=0,
        help="Choose professional category order",
    )
