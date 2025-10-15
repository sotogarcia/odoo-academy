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
        order = f"{field_name}, sequence NULLS LAST, id"
        assignment_set = assignment_obj.search(domain, order=order)

        result = {ass.id: teacher_obj.browse() for ass in assignment_set}
        for assignment in assignment_set:
            key = getattr(assignment, field_name).id
            result.setdefault(key, assignment.teacher_id)

        return result

    # @api.model
    # def _ensure_records(self, targets, model_name, raise_on_error=False):
    #     if not targets:
    #         return self.env[model_name].browse()

    #     if isinstance(targets, models.Model):
    #         if targets._name == model_name:
    #             return targets

    #         if raise_on_error:
    #             message = self.env._(
    #                 "Expected model %(exp)s, got %(got)s"
    #             ) % {"exp": model_name, "got": targets._name}
    #             raise ValidationError(message)

    #         return self.env[model_name].browse()

    #     if isinstance(targets, int):
    #         return self.env[model_name].browse(targets)

    #     if isinstance(targets, (list, tuple, set)):
    #         if all(isinstance(x, int) for x in targets):
    #             return self.env[model_name].browse(list(targets))
    #         if raise_on_error:
    #             message = self.env._("IDs list must contain integers only")
    #             raise ValidationError(message)

    #         return self.env[model_name].browse()

    #     if raise_on_error:
    #         message = self.env._(
    #             "Unsupported targets type: %(typ)s"
    #         ) % {"typ": type(targets).__name__}
    #         raise ValidationError(message)

    #     return self.env[model_name].browse()

    # def init(self):
    #     """Ensure a supporting composite index exists for queries that
    #     order by (training_action_id, sequence, id)."""
    #     # Composite index fields, in the same order used by the query
    #     fields = ["training_action_id", "sequence", "id"]

    #     index_name = f"{self._table}__primary_teacher_idx"

    #     create_index(
    #         self.env,
    #         self._table,
    #         fields=fields,
    #         unique=False,
    #         name=index_name,
    #     )

    # @api.model
    # def _normalize_sequence(self, training_action_ids=None):
    #     """Reassign teacher-assignment sequences for the given actions.

    #     Ensures that all records of this model related to the provided
    #     actions have a strictly consecutive ``sequence`` starting at 1.
    #     Ordering uses current ``sequence`` (NULLS LAST) and then ``id``.

    #     Args:
    #         training_action_ids (list[int] | None): Training action IDs to
    #             normalize. If None or empty, nothing is done.
    #     """
    #     if not training_action_ids:
    #         return

    #     sql = f"""
    #         WITH ranked AS (
    #           SELECT
    #             "id" AS link_id,
    #             ROW_NUMBER() OVER (wnd) AS new_sequence
    #           FROM {self._table}
    #           WHERE training_action_id = ANY(%s)
    #           WINDOW wnd AS (
    #             PARTITION BY training_action_id
    #             ORDER BY "sequence" NULLS LAST, "id" ASC
    #           )
    #         )
    #         UPDATE {self._table} AS link AS link
    #         SET "sequence" = ranked.new_sequence
    #         FROM ranked
    #         WHERE ranked.link_id = link."id"
    #     """

    #     self.env.cr.execute(sql, (training_action_ids,))
