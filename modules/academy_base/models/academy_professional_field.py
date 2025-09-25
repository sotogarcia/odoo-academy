# -*- coding: utf-8 -*-
""" AcademyProfessionalField

This module contains the academy.professional.field Odoo model which stores
all professional field attributes and behavior.
"""

from odoo import models, fields

from logging import getLogger

_logger = getLogger(__name__)


class AcademyProfessionalField(models.Model):
    """Professional field is a property of the training activity"""

    _name = "academy.professional.field"
    _description = "Academy professional field"

    _inherit = ["image.mixin"]

    _rec_name = "name"
    _order = "name ASC"

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Enter new name",
        size=255,
        translate=True,
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Enter new description",
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

    code = fields.Char(
        string="Code",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Enter new code",
        size=8,
        translate=False,
    )

    professional_sector_ids = fields.One2many(
        string="Professional sectors",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="List of sectors related with this professional field.",
        comodel_name="academy.professional.sector",
        inverse_name="professional_field_id",
        domain=[],
        context={},
        auto_join=False,
    )
