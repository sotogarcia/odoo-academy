# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from ..utils.record_utils import get_active_records, has_changed
from odoo.exceptions import UserError
from ..utils.record_utils import DATE_FORMAT
from odoo.osv.expression import TRUE_DOMAIN, FALSE_DOMAIN
from ..utils.helpers import OPERATOR_MAP, many2many_count

from logging import getLogger
from datetime import date


_logger = getLogger(__name__)


class AcademyTrainingActionEnrolmentWizard(models.TransientModel):
    """Massive actions over enrolments"""

    _name = "academy.training.action.enrolment.wizard"
    _description = "Academy training action enrolment wizard"

    _rec_name = "id"
    _order = "id DESC"

    # -------------------------------------------------------------------------
    # Field: enrolment_ids
    # -------------------------------------------------------------------------

    enrolment_ids = fields.Many2many(
        string="Enrolments",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name="academy.training.action.enrolment",
        relation="academy_training_action_enrolment_wizard_enrolment_rel",
        column1="wizard_id",
        column2="enrolment_id",
        domain=[],
        context={},
    )

    enrolment_count = fields.Integer(
        string="Enrolment count",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help="Number of enrolments on whom the action will be carried out",
    )

    # -------------------------------------------------------------------------
    # Field: student_ids
    # -------------------------------------------------------------------------

    student_ids = fields.Many2many(
        string="Students",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name="academy.student",
        relation="academy_training_action_enrolment_wizard_student_rel",
        column1="wizard_id",
        column2="student_id",
        domain=[],
        context={},
    )

    student_count = fields.Integer(
        string="Student count",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help="Number of different students in the selected enrolments",
    )

    # -------------------------------------------------------------------------
    # Field: training_action_ids
    # -------------------------------------------------------------------------

    training_action_ids = fields.Many2many(
        string="Training actions",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name="academy.training.action",
        relation="academy_training_action_enrolment_wizard_training_rel",
        column1="wizard_id",
        column2="training_action_id",
        domain=[],
        context={},
    )

    training_action_count = fields.Integer(
        string="Training action count",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help="Number of different training actions in the selected enrolments",
    )

    # -------------------------------------------------------------------------
    # Field: update_date_start
    # -------------------------------------------------------------------------

    update_date_start = fields.Boolean(
        string="Update date_start",
        required=False,
        readonly=False,
        index=False,
        default=False,
        help="Check it to update enrolemnt date_start date",
    )

    @api.onchange("update_date_start")
    def _onchange_update_date_start(self):
        if self.update_date_start:
            start_list = self.enrolment_ids.mapped("date_start")
            self.date_start = min(start_list) if start_list else date.today()
        else:
            self.date_start = None

    date_start = fields.Datetime(
        string="Date date_start",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Start date date will be set for all the selected enrolments",
    )

    update_date_stop = fields.Boolean(
        string="Update date stop",
        required=False,
        readonly=False,
        index=False,
        default=False,
        help="Check it to update enrolemnt date stop",
    )

    @api.onchange("update_date_stop")
    def _onchange_update_date_stop(self):
        if self.update_date_stop:
            end_list = self.enrolment_ids.mapped("date_stop")
            self.date_stop = min(end_list) if end_list else date.today()
        else:
            self.date_stop = None

    date_stop = fields.Datetime(
        string="Date date_stop",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="End date date will be set for all the selected enrolments",
    )

    # -------------------------------------------------------------------------
    # Field: training_modality_action
    # -------------------------------------------------------------------------

    update_modalities = fields.Boolean(
        string="Update modalities",
        required=False,
        readonly=False,
        index=False,
        default=False,
        help="Check it to update enrolemnt training modalities",
    )

    @api.onchange("update_modalities")
    def _onchange_update_modalities(self):
        self.training_modality_id = None

        training_action_set = self.mapped("enrolment_ids.training_action_id")
        modality_set = training_action_set.mapped("training_modality_id")

        if modality_set:
            for action in training_action_set:
                modality_set &= action.training_modality_id

            if self.update_modalities and len(modality_set) == 1:
                self.training_modality_id = modality_set

    # -------------------------------------------------------------------------
    # Field: available_training_modality_ids
    # -------------------------------------------------------------------------

    # Modalities allowed across all enrolments' actions (intersection).
    available_training_modality_ids = fields.Many2many(
        string="Available modalities",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Modalities allowed across all related training actions.",
        comodel_name="academy.training.modality",
        compute="_compute_available_training_modality_ids",
        store=False,
    )

    @api.depends(
        "enrolment_ids",
        "enrolment_ids.training_action_id",
        "enrolment_ids.training_action_id.training_modality_id",
    )
    def _compute_available_training_modality_ids(self):
        """Compute intersection of modalities across all actions."""
        modality_obj = self.env["academy.training.modality"]
        empty = modality_obj.browse([])

        for record in self:
            actions = record.mapped("enrolment_ids.training_action_id")
            if not actions:
                record.available_training_modality_ids = empty
                continue

            modalities = actions[0].training_modality_id
            for action in actions[1:]:
                modalities = modalities & action.training_modality_id
                if not modalities:
                    break

            record.available_training_modality_ids = modalities

    # -------------------------------------------------------------------------
    # Field: training_modality_ids
    # -------------------------------------------------------------------------

    training_modality_id = fields.Many2one(
        string="Training modality",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Training modalities will be set for all the target enrolments",
        comodel_name="academy.training.modality",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    # -------------------------------------------------------------------------
    # Field: update_material
    # -------------------------------------------------------------------------

    update_material = fields.Boolean(
        string="Update material",
        required=False,
        readonly=False,
        index=False,
        default=False,
        help="Check it to update enrolemnt material",
    )

    @api.onchange("update_material")
    def _onchange_update_material(self):
        material = self.mapped("enrolment_ids.material_status")
        self.material_status = material[0] if len(material) == 1 else None

    # -------------------------------------------------------------------------
    # Field: material
    # -------------------------------------------------------------------------

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

    # -------------------------------------------------------------------------
    # Field: state
    # -------------------------------------------------------------------------

    state = fields.Selection(
        string="State",
        required=True,
        readonly=False,
        index=False,
        default="main",
        help="Allow to choose wizard step",
        selection=[
            ("main", "Main"),
            ("students", "Students"),
            ("training", "Training"),
        ],
    )

    # -------------------------------------------------------------------------
    # Method: perform_action
    # -------------------------------------------------------------------------

    def _perform_action(self):
        self.ensure_one()

        values = {}

        if self.update_date_start:
            date_start_str = self.date_start.strftime(DATE_FORMAT)
            values["register"] = date_start_str

        if self.update_date_stop:
            if self.date_stop:
                date_stop_str = self.date_stop.strftime(DATE_FORMAT)
            else:
                date_stop_str = None
            values["deregister"] = date_stop_str

        if self.update_modalities:
            values["training_modality_id"] = (
                self.training_modality_id.id
                if self.training_modality_id
                else None
            )

        if self.update_material:
            values["material_status"] = self.material_status

        if values:
            ids = self.enrolment_ids.ids
            _logger.info(_(f"Enrolments({ids}) massive update: {values}"))
            self.enrolment_ids.write(values)
        else:
            _logger.info(_("Enrolments massive update: {}"))

    def perform_action(self):
        for record in self:
            record._perform_action()

    # -- Defaults
    # -------------------------------------------------------------------------

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)

        active_set = self.env["academy.training.action.enrolment"]

        active_set = get_active_records(self.env)
        if active_set and active_set._name != active_set._name:
            if hasattr(active_set, "enrolment_id"):
                active_set = active_set.mapped("enrolment_id.id")
            elif hasattr(active_set, "enrolment_ids"):
                active_set = active_set.mapped("enrolment_ids.id")
            else:
                msg = _('Provided object "{}" has not enrolments')
                raise UserError(msg.format(active_set._name))

        enrol_ops = [(6, 0, active_set.ids)] if active_set else [(5, 0, 0)]
        defaults["enrolment_ids"] = enrol_ops
        defaults["enrolment_count"] = len(active_set)

        student_ids = active_set.mapped("student_id").ids
        student_ops = [(6, 0, student_ids)] if student_ids else [(5, 0, 0)]
        defaults["student_ids"] = student_ops
        defaults["student_count"] = len(student_ids)

        action_ids = active_set.mapped("training_action_id").ids
        action_ops = [(6, 0, action_ids)] if action_ids else [(5, 0, 0)]
        defaults["training_action_ids"] = action_ops
        defaults["training_action_count"] = len(action_ids)

        return defaults
