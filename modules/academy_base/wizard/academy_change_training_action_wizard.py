# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class AcademyChangeTrainingActionWizard(models.Model):
    _name = "academy.change.training.action.wizard"
    _description = "Academy change training action wizard"

    _rec_name = "id"
    _order = "id DESC"

    enrolment_ids = fields.Many2many(
        string="Enrolments",
        required=True,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name="academy.training.action.enrolment",
        relation="academy_change_training_action_wizard_enrolment_rel",
        column1="wizard_id",
        column2="enrolment_id",
        domain=[],
        context={},
    )

    training_action_id = fields.Many2one(
        string="Training action",
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name="academy.training.action",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    register = fields.Datetime(
        string="Registration",
        required=True,
        readonly=False,
        index=True,
        default=lambda self: fields.Datetime.now(),
        help="Date the enrolment becomes effective",
        tracking=True,
    )

    deregister = fields.Datetime(
        string="Deregistration",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Date the enrolment ends (leave empty if still ongoing)",
        tracking=True,
    )

    training_modality_id = fields.Many2one(
        string="Training modality",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Learning modality for this enrolment",
        comodel_name="academy.training.modality",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    material_status = fields.Selection(
        string="Material",
        required=True,
        readonly=False,
        index=True,
        default="na",
        help="Current status of material delivery.",
        selection=[
            ("pending", "Pending Delivery"),
            ("delivered", "Material Delivered"),
            ("na", "Not Applicable / Digital"),
        ],
    )

    full_enrolment = fields.Boolean(
        string="Full enrolment",
        required=False,
        readonly=False,
        index=True,
        default=False,
        help="If active, the student will be automatically enrolled in all "
        "modules of the training program.",
    )
