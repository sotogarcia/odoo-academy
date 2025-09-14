# -*- coding: utf-8 -*-
""" AcademyProfessionalSector

This module contains the academy.professional.sector Odoo model which stores
all professional sector attributes and behavior.
"""

from odoo import models, fields

from logging import getLogger

_logger = getLogger(__name__)


class AcademyProfessionalSector(models.Model):
    """Professional sector is a property of the training activity"""

    _name = "academy.professional.sector"
    _description = "Academy professional sector"

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
        help="Enables/disables the record",
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

    professional_field_id = fields.Many2one(
        string="Professional field",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Choose related professional field",
        comodel_name="academy.professional.field",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )
