###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from uuid import uuid4

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
from odoo.tools.translate import _

from ..utils.helpers import one2many_count, one2many_count_search_domain


class AcademyTrainingActionLine(models.Model):
    """
    Represents a snapshot of a training programme line within
    a specific training action. This model ensures that changes
    in the original programme do not affect past or ongoing actions,
    preserving historical consistency.
    """

    _name = "academy.training.action.line"
    _description = "Training action line"

    _inherit = ["academy.training.program.line"]  # noqa: RUF012

    _rec_name = "name"
    _order = "sequence ASC, name"
    _rec_names_search = ["name", "code"]  # noqa: RUF012

    @property
    def shared_keys(self):
        return self.env["academy.training.program.line"].shared_keys

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
        ondelete="set null",
        auto_join=False,
        copy=True,
        tracking=True,
    )

    training_program_id = fields.Many2one(
        string="Training program",
        help="Training program of the original program line (read-only).",
        related="training_action_id.training_program_id",
        required=False,
        store=True,
        copy=True,
    )

    # Override of program's field to rename the M2M relation table
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
        copy=True,
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
        copy=False,
    )

    # -- Teacher assignment: fields and logic
    # -------------------------------------------------------------------------

    teacher_assignment_ids = fields.One2many(
        string="Teacher assignments",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Teacher assignments; order defines primary.",
        comodel_name="academy.training.teacher.assignment",
        inverse_name="action_line_id",
        domain=[],
        context={},
        auto_join=False,
        copy=False,
    )

    primary_teacher_id = fields.Many2one(
        string="Lead",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help="Primary teacher (lowest sequence).",
        comodel_name="academy.teacher",
        domain=[],
        context={},
        ondelete="set null",
        auto_join=False,
        compute="_compute_primary_teacher_id",
        store=True,
        copy=False,
        tracking=True,
    )

    @api.depends(
        "teacher_assignment_ids",
        "teacher_assignment_ids.sequence",
        "teacher_assignment_ids.teacher_id",
        "teacher_assignment_ids.teacher_id.active",
        "teacher_assignment_ids.action_line_id",
    )
    def _compute_primary_teacher_id(self):
        """Compute the primary active teacher for each action line."""
        assignment_obj = self.env["academy.training.teacher.assignment"]
        primary_dict = assignment_obj.get_primary(self)

        for record in self:
            record.primary_teacher_id = primary_dict.get(record.id)

    teacher_assignment_count = fields.Integer(
        string="No. of teachers",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help=False,
        compute="_compute_teacher_assignment_count",
        search="_search_teacher_assignment_count",
        copy=False,
    )

    @api.depends("teacher_assignment_ids")
    def _compute_teacher_assignment_count(self):
        counts = one2many_count(self, "teacher_assignment_ids")

        for record in self:
            record.teacher_assignment_count = counts.get(record.id, 0)

    @api.model
    def _search_teacher_assignment_count(self, operator, value):
        return one2many_count_search_domain(
            self,
            "teacher_assignment_ids",
            operator,
            value,
        )

    needs_synchronization = fields.Boolean(
        string="Para sincronizar",
        required=False,
        readonly=True,
        index=True,
        default=True,
        help="True if the line has changed since the last time it was "
        "sychronized.",
    )

    # -- Constraints
    # -------------------------------------------------------------------------

    _sql_constraints = [  # noqa: RUF012
        (
            "code_unique",  # Same name as program to overload it
            "UNIQUE(code, training_action_id)",
            "Program line must be unique by training action",
        ),
        (
            "non_negative_hours",
            "CHECK(hours >= 0)",
            "Hours must be a non-negative number",
        ),
    ]

    @api.constrains("code", "is_section")
    def _check_code(self):
        message = _("The code is mandatory for the training program lines.")

        for record in self:
            if not record.code and not record.is_section:
                raise ValidationError(message)

    # -- Copy method and auxiliaty methods ------------------------------------

    def copy(self, default=None):
        """Duplicate the action line into another training action.

        The target training action must be different from the source action.
        The original line code is preserved unless explicitly overridden.

        Args:
            default (dict | None): Values to override on the duplicated line.
                The target action can be supplied through
                ``training_action_id``. Defaults to None.

        Returns:
            academy.training.action.line: Newly created action line.

        Raises:
            ValidationError: If no target training action is provided or if
                the target is the current training action.
        """
        self.ensure_one()

        default = dict(default or {})

        self._ensure_new_training_action_on_copy(default)

        if "code" not in default:
            default["code"] = self.code

        action_id = default["training_action_id"]

        if "teacher_assignment_ids" not in default:
            self._copy_teacher_assignments(default, action_id)

        return super().copy(default)

    @api.model_create_multi
    def create(self, values_list):
        """Overridden method 'create'"""

        for values in values_list:
            values.setdefault("code", uuid4().hex[:8])

        return super().create(values_list)

    def write(self, values):
        """Overridden method 'write'"""

        if any(key in self.shared_keys for key in values):
            values["needs_synchronization"] = True

        result = super().write(values)

        return result

    def _ensure_new_training_action_on_copy(self, default):
        """Ensure a different target action is used when duplicating a line.

        The target action is taken first from ``default`` and, if absent, from
        ``default_training_action_id`` in the context.

        Args:
            default (dict): Values that will be passed to ``copy``.

        Returns:
            None

        Raises:
            ValidationError: If no target training action is supplied or if it
                is the same action as the source line.
        """
        action_id = default.get("training_action_id")

        if isinstance(action_id, models.BaseModel):
            action_id.ensure_one()
            action_id = action_id.id

        if not action_id:
            action_id = self.env.context.get("default_training_action_id")

        if isinstance(action_id, models.BaseModel):
            action_id.ensure_one()
            action_id = action_id.id

        if not action_id:
            raise ValidationError(
                _(
                    "A training action is required to duplicate this line. "
                    "Provide it via context as 'default_training_action_id' "
                    "or in defaults as 'training_action_id'."
                )
            )

        if action_id == self.training_action_id.id:
            raise ValidationError(
                _(
                    "Cannot duplicate into the same training action. "
                    "Please choose a different target action."
                )
            )

        default["training_action_id"] = action_id

    def _copy_teacher_assignments(self, default, training_action_id):
        if isinstance(training_action_id, models.BaseModel):
            training_action_id = training_action_id.id

        o2m_ops = [(5, 0, 0)]
        for assign in self.teacher_assignment_ids:
            values = {
                "training_action_id": training_action_id,
                "teacher_id": assign.teacher_id.id,
                "sequence": assign.sequence,
            }
            o2m_ops.append((0, 0, values))

        default["teacher_assignment_ids"] = o2m_ops

    # -- Public methods
    # -------------------------------------------------------------------------

    def view_teacher_assignments(self):
        self.ensure_one()

        name = self.env._("Teachers: {}").format(self.display_name)

        action_xid = "academy_base.action_teacher_assignment_act_window"
        act_wnd = self.env.ref(action_xid)

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))
        context.update(
            {
                "default_training_action_id": self.training_action_id.id,
                "default_action_line_id": self.id,
            }
        )

        domain = [("action_line_id", "=", self.id)]

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": act_wnd.res_model,
            "target": "current",
            "name": name,
            "view_mode": act_wnd.view_mode,
            "domain": domain,
            "context": context,
            "search_view_id": act_wnd.search_view_id.id,
            "help": act_wnd.help,
        }

        return serialized

    # -- Auxiliary methods
    # -------------------------------------------------------------------------

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

        # Fill in with the non-copyable field values
        for index in range(len(program_lines)):
            source_values[index]["code"] = program_lines[index].code

        # Keep only keys that exist in the current model
        return [
            {k: v for k, v in values.items() if k in target_fields}
            for values in source_values
        ]
