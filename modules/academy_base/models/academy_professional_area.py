# -*- coding: utf-8 -*-
""" AcademyProfessionalArea

This module contains the academy.professional.area Odoo model which stores
all Professional Area attributes and behavior.
"""

from odoo import models, fields

from logging import getLogger

_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyProfessionalArea(models.Model):
    """Professional area is a property of the training program"""

    _name = "academy.professional.area"
    _description = "Academy professional area"

    _inherit = ["image.mixin"]

    _rec_name = "name"
    _order = "name ASC"

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Official name of the Professional Area",
        size=255,
        translate=True,
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Detailed description of the Professional Area",
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

    professional_family_id = fields.Many2one(
        string="Professional family",
        required=True,
        readonly=False,
        index=False,
        default=None,
        help="Choose the professional family to which this area belongs",
        comodel_name="academy.professional.family",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    professional_qualification_ids = fields.One2many(
        string="Professional qualifications",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name="academy.professional.qualification",
        inverse_name="professional_area_id",
        domain=[],
        context={},
        auto_join=False,
    )
