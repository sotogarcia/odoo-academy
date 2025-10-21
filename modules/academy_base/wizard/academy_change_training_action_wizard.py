# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError
from ..utils.record_utils import ensure_recordset, get_active_records
from ..utils.helpers import post_note

from datetime import datetime, date
from pytz import utc, timezone
from logging import getLogger

_INFINITY = datetime.max
_ENROLMENT = "academy.training.action.enrolment"

MSG_TO = "Automatically terminated due to reassignment to training action: {}."
MSG_FROM_1 = "Enrolment transferred from the previous training action: {}."
MSG_FROM_N = "Enrolment transferred as part of a bulk reassignment operation."

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
        help="Enrolments to be reassigned to another training action.",
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
        help="Target training action for the selected enrolments.",
        comodel_name="academy.training.action",
        domain=[("child_ids", "=", False)],
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
    )

    deregister = fields.Datetime(
        string="Deregistration",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Date the enrolment ends (leave empty if still ongoing)",
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

    # -- Onchange
    # -------------------------------------------------------------------------

    @api.onchange("training_action_id")
    def _onchange_training_action_id(self):
        action = self.training_action_id
        if action:
            now = fields.Datetime.now()

            lbound = action.date_start or datetime.min
            ubound = action.date_stop or datetime.max
            self.register = min(ubound, max(lbound, now))
            self.deregister = action.date_stop

            modality = self.training_action_id.training_modality_id
            self.training_modality_id = modality

            self.material_status = "na"
            self.full_enrolment = True

    # -- Overloaded methods
    # -------------------------------------------------------------------------

    @api.model
    def default_get(self, fields):
        values = super().default_get(fields)

        if "enrolment_ids" in fields and not values.get("enrolment_ids"):
            enrolment_set = get_active_records(self.env, _ENROLMENT)
            if enrolment_set:
                values["enrolment_ids"] = enrolment_set.ids

        return values

    # -- Wizard execution entry point
    # -------------------------------------------------------------------------

    def perform_action(self):
        enrolment_set = self.env[_ENROLMENT].browse()
        for record in self:
            enrolment_set |= record.change_training_action(
                record.enrolment_ids,
                record.training_action_id,
                register=record.register,
                deregister=record.deregister,
                training_modality_id=record.training_modality_id.id,
                material_status=record.material_status,
                full_enrolment=record.full_enrolment,
            )

    # -- Public hooks
    # -------------------------------------------------------------------------

    @api.model
    def before_change_training_action(
        self, enrolments, training_action, **kwargs
    ):
        """Extension hook called before enrolment reassignment.

        Can be overridden by inherited models to implement custom
        pre-processing logic, validations, or context adjustments.

        Args:
            enrolments (recordset): Enrolments to be reassigned.
            training_action (recordset): Target training action.
            **kwargs: Additional keyword arguments passed to the main method.
        """
        return

    @api.model
    def after_change_training_action(
        self, old_enrolments, new_enrolments, training_action, **kwargs
    ):
        """Extension hook called after enrolment reassignment.

        This method can be overridden by inherited models to perform
        additional logic such as logging, analytics, notifications,
        or external integrations.

        Args:
            old_enrolments (recordset): Enrolments that were terminated.
            new_enrolments (recordset): Enrolments that were newly created.
            training_action (recordset): Target training action record.
            **kwargs: Additional parameters passed to the main method.
        """
        return

    # -- Public @api.model method: change_training_action
    # -- and all its auxiliary methods and logic
    # -------------------------------------------------------------------------

    @api.model
    def change_training_action(self, enrolments, training_action, **kwargs):
        """Reassign students to a different training action.

        This method takes existing enrolment records and transfers the
        corresponding students to the given training action. It performs
        a sequence of validation and transformation steps to ensure data
        integrity and temporal consistency.

        Args:
            enrolments (recordset|list|int):
                Existing enrolments to be transferred.
            training_action (recordset|int):
                Target training action record.
            **kwargs:
                Optional overrides for default enrolment values such as
                ``register``, ``deregister``, ``material_status``,
                or ``full_enrolment``.

        Returns:
            recordset: Newly created ``academy.training.action.enrolment``
            records associated with the target training action.
        """
        self_ctx = self.with_context(active_test=False)

        old_enrolments = self.env[_ENROLMENT].browse()
        new_enrolments = self.env[_ENROLMENT].browse()

        # 1.  Ensure `enrolments` is a valid enrolment recordset
        enrolment_set = ensure_recordset(self_ctx.env, enrolments, _ENROLMENT)
        if not enrolment_set:
            return new_enrolments

        # 2. Ensure `training_action` is a single training action record
        training_action = ensure_recordset(
            self_ctx.env, training_action, "academy.training.action"
        )
        training_action.ensure_one()

        # 3. Invoke pre-change hook for extensions
        self.before_change_training_action(
            enrolments=enrolment_set,
            training_action=training_action,
            **kwargs,
        )

        # 4. Merge enrolment default values with optional keyword arguments.
        defaults = self._process_defaults(training_action, **kwargs)

        # 5. Validate that enrolment dates fall within the action’s interval.
        self._ensure_within_training_interval(training_action, **defaults)

        # 6. Detect and prevent conflicting reassignment cases.
        #    These will raise a ValidationError. See documentation:
        #    academy_base/static/docs/enrollment_reassignment.md
        self._ensure_no_conflicting_records(enrolment_set, training_action)

        # 7. Terminate all active enrolments within processable recordset.
        date_change = defaults.get("register", datetime.now)
        old_enrolments = self._finish_enrolments(enrolment_set, date_change)
        self._post_note_changed_to(enrolment_set, training_action)

        # 8. Create new enrolments for all affected students
        student_set = enrolment_set.mapped("student_id")
        new_enrolments = self._create_enrolments(student_set, defaults)
        self._post_note_changed_from(new_enrolments, enrolment_set)

        # 9. Invoke post-change hook for extensions
        self.after_change_training_action(
            old_enrolments=old_enrolments,
            new_enrolments=new_enrolments,
            training_action=training_action,
            **kwargs,
        )

        return new_enrolments

    @staticmethod
    def _get_company_tz(training_action, default=None):
        """Return timezone name for the company owning the training action.

        Falls back to the provided default (usually user.tz) or to UTC.
        """
        tz_name = None
        if training_action and training_action.company_id:
            tz_name = training_action.company_id.partner_id.tz

        # Fallback chain: company → default → UTC
        return tz_name or default or "UTC"

    @api.model
    def _local_midnight(self, training_action):
        """Compute midnight in the training action's company timezone.

        If the company's timezone is undefined, falls back to the user's
        timezone, and finally to UTC.
        """
        midnight_args = dict(hour=0, minute=0, second=0, microsecond=0)
        tz_name = self._get_company_tz(training_action, self.env.user.tz)

        try:
            local_tz = timezone(tz_name)
        except Exception:
            local_tz = timezone("UTC")

        naive_now = fields.Datetime.now()
        utc_now = naive_now.replace(tzinfo=utc)

        local_now = utc_now.astimezone(local_tz)
        local_midnight = local_now.replace(**midnight_args)

        utc_midnight = local_midnight.astimezone(utc)
        naive_midnight = utc_midnight.replace(tzinfo=None)

        return naive_midnight

    @api.model
    def _process_defaults(self, training_action, **kwargs):
        """Build default values for new enrolments based on the given
        training action and optional overrides."""

        values = kwargs or {}

        register = values.get("register", False)
        if not register:
            register = self._local_midnight(training_action)
        elif isinstance(register, (date, datetime, str)):
            register = fields.Datetime.to_datetime(register)

        deregister = values.get("deregister", None)
        if isinstance(deregister, (date, datetime, str)):
            deregister = fields.Datetime.to_datetime(deregister)

        training_modality_id = values.get("training_modality_id", None)
        if not training_modality_id:
            training_modality_id = training_action.training_modality_id.id
        elif isinstance(training_modality_id, models.Model):
            training_modality_id = training_modality_id.id
        elif isinstance(training_modality_id, (list, tuple)):
            training_modality_id = training_modality_id[0]

        material_status = values.get("material_status", "na")
        full_enrolment = values.get("full_enrolment", True)

        return {
            "training_action_id": training_action.id,
            "register": register,
            "deregister": deregister,
            "training_modality_id": training_modality_id,
            "material_status": material_status,
            "full_enrolment": full_enrolment,
        }

    @staticmethod
    def _ensure_within_training_interval(training_action, **kwargs):
        """Validate that enrolment dates fall within the training
        action's start and end dates."""

        values = kwargs or {}

        action_start = training_action.date_start
        if not action_start:
            raise ValidationError(_("Training action has no start date."))

        action_stop = training_action.date_stop or _INFINITY

        enrol_start = values.get("register")
        if not enrol_start:
            raise ValidationError(_("Missing enrolment start date."))

        enrol_stop = values.get("deregister", False) or _INFINITY

        if action_start > enrol_start or action_stop < enrol_stop:
            message = _(
                "<Enrolment> dates are outside the training action's period. "
                "The registration must start on or after "
                "'%s' and stop on or before '%s'."
            ) % (
                action_start.strftime("%Y-%m-%d"),
                action_stop.strftime("%Y-%m-%d"),
            )
            raise ValidationError(message)

    @staticmethod
    def _ensure_no_conflicting_records(enrolment_set, training_action):
        """Raise an error if any enrolment already belongs to the
        target training action."""

        if not enrolment_set:
            return

        training_action.ensure_one()
        conflicting_set = enrolment_set.filtered(
            lambda e: e.training_action_id == training_action
        )
        if conflicting_set:
            raise ValidationError(
                _(
                    "Some enrolments already belong to the target training "
                    "action. Please review them before reassigning."
                )
            )

    @api.model
    def _finish_enrolments(self, enrolment_set, date_change=None):
        """Set the deregistration date to now for all ongoing enrolments
        whose deregistration date is unset or later than the current time."""

        date_change = date_change or fields.Datetime.now()
        date_change_str = fields.Datetime.to_string(date_change)

        # Select enrolments without deregister or with a future deregister date
        to_terminate = enrolment_set.filtered(
            lambda e: not e.deregister or e.deregister > date_change
        )
        if not to_terminate:
            return

        # Split between those already started and those not yet started
        to_finish_enrolments = to_terminate.filtered(
            lambda e: e.register <= date_change
        )
        to_terminate_later = to_terminate - to_finish_enrolments

        if to_finish_enrolments:
            to_finish_enrolments.write({"deregister": date_change_str})

        if to_terminate_later:
            for enrol in to_terminate_later:
                start_str = fields.Datetime.to_string(enrol.register)
                enrol.write({"deregister": start_str})

        _logger.info(
            "Terminated %d enrolments (%d on date, %d scheduled).",
            len(to_terminate),
            len(to_finish_enrolments),
            len(to_terminate_later),
        )

    def _create_enrolments(self, student_set, defaults):
        """Create new enrolment records for the given students using the
        provided default values."""

        enrolment_obj = self.env[_ENROLMENT]
        new_enrolments = enrolment_obj.browse()

        if student_set:
            defaults = defaults or {}
            values_list = []
            for student in student_set:
                if student and isinstance(student.id, int):
                    values = defaults.copy()
                    values["student_id"] = student.id
                    values_list.append(values)

            if values_list:
                new_enrolments = enrolment_obj.create(values_list)

        _logger.info("Created %d enrolments", len(new_enrolments))

        return new_enrolments

    @staticmethod
    def _post_note_changed_to(enrolment_set, training_action):
        action_name = training_action.display_name or _("Unknown action")
        post_note(enrolment_set, MSG_TO, action_name)

    @staticmethod
    def _post_note_changed_from(new_enrolments, old_enrolments):
        # Post a note in chatter for all new enrolments
        source_actions = old_enrolments.mapped("training_action_id")
        if len(source_actions) == 1:
            action_name = source_actions.display_name or _("Unknown action")
            post_note(new_enrolments, MSG_FROM_1, action_name)
        else:
            post_note(new_enrolments, MSG_FROM_N)
