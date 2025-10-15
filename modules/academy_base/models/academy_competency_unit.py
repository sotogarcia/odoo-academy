# -*- coding: utf-8 -*-
""" AcademyCompetencyUnit

This module contains the academy.competency.unit Odoo model which stores
all competency unit attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from ..utils.helpers import sanitize_code
from odoo.exceptions import ValidationError

from logging import getLogger

_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyCompetencyUnit(models.Model):
    """Competence Standard stores the specific name will be used by a module in
    a training program
    """

    _name = "academy.competency.unit"
    _description = "Academy competency unit"

    _rec_name = "name"
    _order = "name ASC"
    _rec_names_search = ["name", "code"]

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Official name of the Professional Competence Standard (ECP)",
        size=1024,
        translate=True,
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Detailed description of the Professional Competence Standard",
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
        index=False,
        default=None,
        help="Official code of the standard (e.g., ECP1720_3)",
        size=30,
        translate=False,
    )

    level = fields.Selection(
        string="Level",
        required=True,
        readonly=False,
        index=True,
        default=False,
        help="Competence level according to the INCUAL catalogue",
        selection=[
            ("L1", "Basic"),
            ("L2", "Medium"),
            ("L3", "Advanced"),
        ],
    )

    professional_family_id = fields.Many2one(
        string="Professional family",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Professional family this standard belongs to",
        comodel_name="academy.professional.family",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    @api.onchange("professional_family_id")
    def _onchange_professional_family_id(self):
        self.professional_area_id = None

    professional_area_id = fields.Many2one(
        string="Professional area",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Professional area within the family",
        comodel_name="academy.professional.area",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    professional_field_id = fields.Many2one(
        string="Professional field",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Professional field associated with the standard",
        comodel_name="academy.professional.field",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    # -------------------------- Contraints -----------------------------------

    _sql_constraints = [
        (
            "code_unique",
            "unique(code)",
            "Module code must be unique",
        ),
    ]

    @api.constrains("professional_area_id")
    def _check_professional_area_id(self):
        message1 = _("Select a professional family before choosing an area")
        message2 = _("Area %s does not belong to family %s.")

        for record in self:
            area = record.professional_area_id
            if not area:
                continue

            family = record.professional_family_id
            if not family:
                raise ValidationError(message1)

            if area.professional_family_id != family:
                raise ValidationError(
                    message2 % (area.display_name, family.display_name)
                )

    # -- Methods overrides ----------------------------------------------------

    @api.model_create_multi
    def create(self, values_list):
        sanitize_code(values_list, "upper")
        return super().create(values_list)

    def write(self, values):
        sanitize_code(values, "upper")
        return super().write(values)
