# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..utils.sql_helpers import create_index

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingActionAssignment(models.Model):
    """Link between a training action and a teacher (optionally a program
    unit).

    Stores the assignment of ``teacher_id`` to a given
    ``training_action_id`` and, optionally, to a specific ``action_line_id``.
    The ``sequence`` field provides a stable, per-action ordering.
    """

    _name = "academy.training.teacher.assignment"
    _description = "Academy training action teacher assignment"

    training_action_id = fields.Many2one(
        string="Training action",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Training action to which this assignment belongs",
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
        help="Program unit within the training action (optional)",
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
        help="Assigned teacher",
        comodel_name="academy.teacher",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    sequence = fields.Integer(
        string="Sequence",
        required=True,
        readonly=False,
        index=True,
        default=0,
        help="Display/relevancy order within the training action",
    )

    # -- Constraints ----------------------------------------------------------

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

    # -- Auxiliary methods ----------------------------------------------------

    def _get_training_action_ids(self):
        """Return the list of involved training action IDs for ``self``."""
        return self.mapped("training_action_id").ids or []

    @api.model
    def get_primary(self, targets):
        mapping = {
            "academy.training.action": "training_action_id",
            "academy.training.action.line": "action_line_id",
        }

        if not isinstance(targets, models.Model):
            raise ValidationError(self.env._("A recordset is required"))

        model_name = targets._name
        if targets._name not in mapping.keys():
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

        result = {ass.id: teacher_obj.browse() for ass in assignment_set}
        for assignment in assignment_set:
            key = getattr(assignment, field_name).id
            result.setdefault(key, assignment.teacher_id)

        return result

    @api.model_create_multi
    def create(self, values_list):
        """Overridden method 'create' to populate training_action_id from action_line_id."""
        self._complete_training_action_from_lines(values_list)

        return super().create(values_list)

    def _complete_training_action_from_lines(self, values_list):
        # 1. Collect action_line_ids where training_action_id is missing
        missing_action_line_ids = set()
        for values in values_list:
            action_id = values.get("training_action_id")
            line_id = values.get("action_line_id", False)
            if not action_id and line_id:
                missing_action_line_ids.add(values["action_line_id"])

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
                line_id = values.get("action_line_id", False)
                if values.get("training_action_id") or not line_id:
                    continue

                action_id = line_to_action_map.get(line_id)
                if action_id:
                    values["training_action_id"] = action_id
