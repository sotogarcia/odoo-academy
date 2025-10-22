# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError, UserError
from ..utils.sql_helpers import create_index

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingActionAssignment(models.Model):
    """Link between a training action and a teacher (optionally a program
    unit).

    Stores the assignment of ``teacher_id`` to a given ``training_action_id``
    and, optionally, to a specific ``action_line_id``.
    The ``sequence`` field provides a stable, per-action ordering.
    """

    _name = "academy.training.teacher.assignment"
    _description = "Academy training action teacher assignment"

    _inherit = ["mail.thread"]

    IMMUTABLE_FIELDS = [
        "training_action_id",
        "action_line_id",
    ]

    training_action_id = fields.Many2one(
        string="Training action",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Training action to which this assignment belongs.",
        comodel_name="academy.training.action",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    action_line_id = fields.Many2one(
        string="Program unit",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Program unit within the training action (optional).",
        comodel_name="academy.training.action.line",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    teacher_id = fields.Many2one(
        string="Teacher",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Assigned teacher.",
        comodel_name="academy.teacher",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        tracking=True,
    )

    sequence = fields.Integer(
        string="Sequence",
        required=True,
        readonly=False,
        index=True,
        default=0,
        help="Display/relevancy order within the training action.",
        tracking=True,
    )

    # -- Constraints
    # -------------------------------------------------------------------------

    def init(self):
        """Uniqueness: by line (when set) else by action (when line is NULL)."""

        # 1) Unique per line+teacher when there is a line
        create_index(
            self.env,
            self._table,
            fields=["action_line_id", "teacher_id"],
            unique=True,
            name=f"{self._table}_uniq_line_teacher",
            where="action_line_id IS NOT NULL",
        )

        # 2) Unique per action+teacher when there is NO line
        create_index(
            self.env,
            self._table,
            fields=["training_action_id", "teacher_id"],
            unique=True,
            name=f"{self._table}_uniq_action_teacher_noline",
            where="action_line_id IS NULL",
        )

    @api.constrains("training_action_id", "action_line_id")
    def _check_action_line_belongs_to_action(self):
        """Ensure the selected program unit is part of the training action."""
        message = self.env._(
            "Program unit must belong to the selected training action."
        )
        for record in self:
            if (
                record.action_line_id
                and record.action_line_id.training_action_id
                and record.action_line_id.training_action_id
                != record.training_action_id
            ):
                raise ValidationError(message)

    # -- Overridden methods
    # -------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, values_list):
        """Populate ``training_action_id`` from ``action_line_id`` and ensure
        the initial chatter message (creation) is forwarded to the most
        specific thread (line if present, else action).
        """

        self._complete_training_action_from_lines(values_list)

        result = super().create(values_list)
        result._forward_messages_to_the_training_item()

        return result

    def write(self, values):
        """Keep coherence when updating ``action_line_id`` and forward
        chatter only if thread-defining fields changed.
        """

        # If a single line is being set for the batch and action is omitted,
        # complete it here (same action will apply to all records in self).
        # This is for future,
        self._complete_training_action_from_single_line(values)

        # Ensure immutability check sees any value completed above
        self._prevent_change_immutable_fields(values)

        result = super().write(values)

        if any(k in values for k in ("action_line_id", "training_action_id")):
            self._forward_messages_to_the_training_item()

        return result

    def copy(self, default=None):
        """
        Overrides the standard copy method to prohibit record duplication.
        Raises a UserError immediately upon attempt.
        """
        err = _("Duplicating records on this model is strictly prohibited.")
        raise UserError(err)

    # -- Auxiliary methods
    # -------------------------------------------------------------------------

    def _prevent_change_immutable_fields(self, vals):
        """
        Helper method to check if immutable fields are being modified.
        It raises a UserError if a field is modified after its initial set.
        """

        error_message = _(
            "The field '%(f)s' cannot be modified once it has been set."
        )

        fields_to_check = set(self.IMMUTABLE_FIELDS) & set(vals.keys())
        if not fields_to_check:
            return True

        for record in self:
            for field_name in fields_to_check:
                new_value = vals[field_name]
                if isinstance(new_value, models.BaseModel):
                    new_value = new_value.id

                current_value = (
                    record[field_name].id if record[field_name] else False
                )

                if current_value and current_value != new_value:
                    raise ValidationError(
                        error_message
                        % {"f": record._fields[field_name].string}
                    )

        return True

    def _forward_messages_to_the_training_item(self):
        """Move chatter to the most specific training thread available."""
        for record in self:
            destination = record.action_line_id or record.training_action_id
            if not destination:
                continue

            # Avoid work if already pointing to the same thread (best effort).
            # message_change_thread is idempotent; calling is safe either way.
            record.message_change_thread(destination)

    def _get_training_action_ids(self):
        """Return the list of involved training action IDs for ``self``."""
        return self.mapped("training_action_id").ids or []

    @api.model
    def get_primary(self, targets):
        """Return the *primary* (first by sequence) active teacher per target
        (action or program unit), as a dict: {target_id: teacher_record}.
        For targets with no assignment, value is an empty recordset.
        """
        mapping = {
            "academy.training.action": "training_action_id",
            "academy.training.action.line": "action_line_id",
        }

        if not isinstance(targets, models.Model):
            raise ValidationError(self.env._("A recordset is required"))

        model_name = targets._name
        if model_name not in mapping.keys():
            message = self.env._("Unsupported model: %s")
            raise ValidationError(message % model_name)

        assignment_obj = self.env[self._name]
        teacher_obj = self.env["academy.teacher"]
        if not targets:
            return teacher_obj.browse()

        field_name = mapping.get(model_name)

        domain = [
            (field_name, "in", targets.ids),
            ("teacher_id.active", "=", True),
        ]
        order = f"{field_name}, sequence NULLS LAST"
        assignment_set = assignment_obj.search(domain, order=order)

        # Seed all targets with empty teacher to ensure total coverage
        result = {t.id: teacher_obj.browse() for t in targets}
        for assignment in assignment_set:
            key = getattr(assignment, field_name).id
            # Keep first (lowest sequence) assignment only
            if not result[key]:
                result[key] = assignment.teacher_id

        return result

    @api.model
    def _complete_training_action_from_lines(self, values_list):
        # 1. Collect action_line_ids where training_action_id is missing
        missing_action_line_ids = set()

        for values in values_list:
            action_id = values.get("training_action_id")
            line_id = values.get("action_line_id") or False
            if not action_id and line_id:
                missing_action_line_ids.add(line_id)

        if missing_action_line_ids:
            # 2. Fetch parent training_action_id in a single query
            line_obj = self.env["academy.training.action.line"]
            line_set = line_obj.search(
                [("id", "in", list(missing_action_line_ids))]
            )

            # 3. Map line ID to parent action ID
            line_to_action_map = {
                line.id: line.training_action_id.id for line in line_set
            }

            # 4. Update values_list with the fetched training_action_id
            for values in values_list:
                line_id = values.get("action_line_id") or False
                if values.get("training_action_id") or not line_id:
                    continue

                action_id = line_to_action_map.get(line_id)
                if action_id:
                    values["training_action_id"] = action_id

    def _complete_training_action_from_single_line(self, values):
        """If a single ``action_line_id`` is provided for the write batch and
        ``training_action_id`` is omitted, inject the parent's action id.
        """
        line_id = values.get("action_line_id")
        if line_id and "training_action_id" not in values:
            line = self.env["academy.training.action.line"].browse(line_id)
            values["training_action_id"] = line.training_action_id.id
