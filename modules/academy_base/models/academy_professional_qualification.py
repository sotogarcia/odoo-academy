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
    """Professional qualification is a property of the training activity"""

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

    competency_unit_ids = fields.One2many(
        string="Academy competency units",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Choose related competency units",
        comodel_name="academy.competency.unit",
        inverse_name="professional_qualification_id",
        domain=[],
        context={},
        auto_join=False,
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

    # --------------------------- MANAGEMENT FIELDS ---------------------------

    # pylint: disable=locally-disabled, W0212
    competency_unit_count = fields.Integer(
        string="Competency units",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help=(
            "Number of competency units related with this professional "
            "qualification"
        ),
        compute="_compute_competency_unit_count",
        search="_search_competency_unit_count",
    )

    @api.depends("competency_unit_ids")
    def _compute_competency_unit_count(self):
        counts = one2many_count(self, "competency_unit_ids")

        for record in self:
            record.reservation_count = counts.get(record.id, 0)

    @api.model
    def _search_competency_unit_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = one2many_count(self.search([]), "competency_unit_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN
