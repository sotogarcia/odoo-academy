# -*- coding: utf-8 -*-
""" AcademyProfessionalQualification

This module contains the academy.professional.qualification Odoo model which
stores all professional qualification attributes and behavior.
"""

from odoo import models, fields, api
from odoo.osv.expression import TRUE_DOMAIN, FALSE_DOMAIN
from ..utils.helpers import OPERATOR_MAP, one2many_count

from logging import getLogger

_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyProfessionalQualification(models.Model):
    """Professional qualification is a property of the training program"""

    _name = "academy.professional.qualification"
    _description = "Academy professional qualification"

    _inherit = ["image.mixin"]

    _rec_name = "name"
    _order = "name ASC"

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Official name of the Professional Qualification",
        size=255,
        translate=True,
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Detailed description of the Professional Qualification",
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
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Choose related professional family",
        comodel_name="academy.professional.family",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    professional_area_id = fields.Many2one(
        string="Professional area",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Choose related professional area",
        comodel_name="academy.professional.area",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    qualification_code = fields.Char(
        string="Internal code",
        required=True,
        readonly=False,
        index=False,
        default=None,
        help="Enter new internal code",
        size=30,
        translate=False,
    )

    qualification_level_id = fields.Many2one(
        string="Qualification level",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Choose related qualification level",
        comodel_name="academy.qualification.level",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )
