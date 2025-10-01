# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingActionLine(models.Model):
    """
    Represents a snapshot of a training programme line within
    a specific training action. This model ensures that changes
    in the original programme do not affect past or ongoing actions,
    preserving historical consistency.
    """

    _name = "academy.training.action.line"
    _description = "Training action line"

    _inherit = ["academy.training.program.line"]

    _rec_name = "name"
    _order = "sequence ASC"
    _rec_names_search = ["name", "code"]

    program_line_id = fields.Many2one(
        string="Program line",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Original program line used as the template for this record.",
        comodel_name="academy.training.program.line",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    training_action_id = fields.Many2one(
        string="Training action",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Training action this line belongs to.",
        comodel_name="academy.training.action",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    training_program_id = fields.Many2one(
        string="Training program",
        help="Training program of the original program line (read-only).",
        related="training_action_id.training_program_id",
        store=True,
    )

    # competency_unit_ids = fields.Many2many(
    #     string="Competence Standards (ECP)",
    #     required=False,
    #     readonly=False,
    #     index=True,
    #     default=None,
    #     help=("Professional Competence Standards (ECP) linked to unit"),
    #     comodel_name="academy.competency.unit",
    #     relation="academy_training_action_line_competency_unit_rel",
    #     column1="action_line_id",
    #     column2="competency_unit_id",
    #     domain=[],
    #     context={},
    # )
