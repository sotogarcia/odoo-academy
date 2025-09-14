# -*- coding: utf-8 -*-
""" AcademyProfessionalFamily

This module contains the academy.professional.family Odoo model which stores
all professional family attributes and behavior.
"""

from odoo import models, fields, api
from odoo.osv.expression import TRUE_DOMAIN, FALSE_DOMAIN
from ..utils.helpers import OPERATOR_MAP, one2many_count

from logging import getLogger

_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyProfessionalFamily(models.Model):
    """Professional family is a property of the training activity"""

    _name = "academy.professional.family"
    _description = "Academy professional family"

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

    professional_area_ids = fields.One2many(
        string="Professional area",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name="academy.professional.area",
        inverse_name="professional_family_id",
        domain=[],
        context={},
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
        inverse_name="professional_family_id",
        domain=[],
        context={},
        auto_join=False,
    )

    # -------------------------- MANAGEMENT FIELDS ----------------------------

    # pylint: disable=locally-disabled, W0212
    professional_area_count = fields.Integer(
        string="Professional areas",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help=(
            "Shows the number of professional areas that belong to this "
            "family"
        ),
        compute="_compute_professional_area_count",
        search="_search_professional_area_count",
    )

    @api.depends("professional_area_ids")
    def _compute_professional_area_count(self):
        counts = one2many_count(self, "professional_area_ids")

        for record in self:
            record.reservation_count = counts.get(record.id, 0)

    @api.model
    def _search_professional_area_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = one2many_count(self.search([]), "professional_area_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN
