# -*- coding: utf-8 -*-
""" AcademyCompetencyUnit

This module contains the academy.competency.unit Odoo model which stores
all competency unit attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools import safe_eval
from odoo.exceptions import UserError

from logging import getLogger

_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyCompetencyUnit(models.Model):
    """Competency unit stores the specific name will be used by a module in
    a training activity
    """

    _name = "academy.competency.unit"
    _description = "Academy competency unit"

    _rec_name = "name"
    _order = "sequence ASC, name ASC"

    name = fields.Char(
        string="Competency name",
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
        help="General description and scope of the standard",
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
        string="Unit code",
        required=False,
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
