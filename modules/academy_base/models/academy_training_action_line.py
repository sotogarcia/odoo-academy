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

    competency_unit_ids = fields.Many2many(
        string="Competence Standards (ECP)",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help=("Professional Competence Standards (ECP) linked to unit"),
        comodel_name="academy.competency.unit",
        relation="academy_training_action_line_competency_unit_rel",
        column1="action_line_id",
        column2="competency_unit_id",
        domain=[],
        context={},
    )

    _sql_constraints = [
        (
            "code_unique",
            "UNIQUE(code, training_action_id)",
            "Program line must be unique by training action",
        ),
        (
            "non_negative_hours",
            "CHECK(hours >= 0)",
            "Hours must be a non-negative number",
        ),
    ]

    def _read_program_line(self, program_lines, defaults=None):
        """
        Extracts writable field values from given program lines,
        returning only those compatible with the current model.

        Args:
            program_lines (recordset):
                Source records whose data will be copied.
            defaults (dict | None):
                Default values to override during copy.

        Returns:
            list[dict]: A list of dictionaries containing filtered field values
                        suitable for write() or create() on the current model.
        """
        defaults = dict(defaults or {})
        target_fields = self._fields

        # returns one dict per record, already handling Command objects
        source_values = program_lines.copy_data(defaults)

        # Keep only keys that exist in the current model
        return [
            {k: v for k, v in values.items() if k in target_fields}
            for values in source_values
        ]

    def update_from_program_line(self):
        """
        Update the current action lines using data from their related
        program lines.

        For each record, field values are copied from its linked
        `program_line_id` through `_read_program_line()`. The result
        is then written back to the current record, keeping both
        models consistent.

        Returns:
            bool: True if at least one record was updated or if no
                  update was needed; False otherwise.
        """
        result = True

        for record in self:
            program_line = record.program_line_id
            if not program_line:
                continue

            values = self._read_program_line(program_line)[0]
            values.update(
                {
                    "training_action_id": record.training_action_id.id,
                    "program_line_id": program_line.id,
                    "comment": None,
                }
            )

            result = result or record.write(values)

        return result

    @api.model
    def create_from_program_line(self, training_action, program_lines):
        """
        Create new training action lines based on the given program lines.

        Args:
            training_action (record):
                The training action that will own the created lines.
            program_lines (recordset):
                Program lines whose data will be copied into action lines.

        Returns:
            recordset: Newly created action line records, or an empty
                       recordset if nothing was created.
        """
        training_action.ensure_one()

        value_list = []
        for program_line in program_lines:
            # _read_program_line expects a recordset, even if single
            values = self._read_program_line(program_line)[0]
            values.update(
                {
                    "training_action_id": training_action.id,
                    "program_line_id": program_line.id,
                    "comment": None,
                }
            )
            value_list.append(values)

        # Bulk create for efficiency; return empty recordset if none
        return self.create(value_list) if value_list else self.browse()
