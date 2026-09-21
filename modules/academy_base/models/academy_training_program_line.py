###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################


from uuid import uuid4

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
from odoo.tools.translate import _

from ..utils.helpers import many2many_count, sanitize_code


class AcademyTrainingProgramLine(models.Model):
    _name = "academy.training.program.line"
    _description = "Academy training program line"

    _inherit = [  # noqa: RUF012
        "ownership.mixin",
        "image.mixin",
        "mail.thread",
        "mail.activity.mixin",
    ]

    _rec_name = "name"
    _order = "sequence ASC, name, id"
    _rec_names_search = ["name", "code"]  # noqa: RUF012

    _SHARED_KEYS = (
        "name",
        "sequence",
        "description",
        "active",
        "code",
        "optional",
        "hours",
        "training_module_id",
        "competency_unit_ids",
        "is_section",
    )

    _SYNCHRONIZATION_KEYS = (
        *_SHARED_KEYS,
        "training_program_id",
    )

    @property
    def shared_keys(self):
        return type(self)._SHARED_KEYS

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Name of the program line; usually the module or block title",
        size=1024,
        translate=True,
        copy=True,
        tracking=True,
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Detailed description of the line content, scope and objectives",
        translate=True,
        copy=True,
    )

    active = fields.Boolean(
        string="Active",
        required=False,
        readonly=False,
        index=False,
        default=True,
        help="Disable to archive without deleting.",
        copy=True,
        tracking=True,
    )

    code = fields.Char(
        string="Code",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Official or internal code for this program line",
        size=30,
        translate=False,
        copy=False,
        tracking=True,
    )

    sequence = fields.Integer(
        string="Sequence",
        required=True,
        readonly=False,
        index=False,
        default=0,
        help="Defines the order in which modules appear inside the program",
        copy=True,
    )

    comment = fields.Html(
        string="Internal notes",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=(
            "Private notes for staff only. Not shown to students, "
            "not exported, and excluded from printed reports."
        ),
        sanitize=True,
        sanitize_attributes=False,
        strip_style=True,
        translate=False,
        copy=False,
    )

    optional = fields.Boolean(
        string="Optional",
        required=False,
        readonly=False,
        index=False,
        default=False,
        help="Mark if this line is optional/elective for the learner",
        copy=True,
        tracking=True,
    )

    hours = fields.Float(
        string="Hours",
        required=False,
        readonly=False,
        index=False,
        default=0.0,
        digits=(16, 2),
        help="Nominal duration of the line in hours",
        copy=True,
        tracking=True,
    )

    training_program_id = fields.Many2one(
        string="Training program",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Training program this line belongs to",
        comodel_name="academy.training.program",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        copy=False,
        tracking=True,
    )

    training_module_id = fields.Many2one(
        string="Training module",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Module or block linked to this program line",
        comodel_name="academy.training.module",
        domain=[],
        context={},
        ondelete="restrict",
        auto_join=False,
        copy=True,
        tracking=True,
    )

    @api.onchange("training_module_id")
    def _onchange_training_module_id(self):
        if self.training_module_id:
            self.hours = self.training_module_id.hours
        else:
            self.hours = 0.0

    competency_unit_ids = fields.Many2many(
        string="Competence Standards (ECP)",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help=("Professional Competence Standards (ECP) linked to unit"),
        comodel_name="academy.competency.unit",
        relation="academy_training_program_line_competency_unit_rel",
        column1="program_line_id",
        column2="competency_unit_id",
        domain=[],
        context={},
        copy=True,
    )

    # -- Computed field: competency_unit_count --------------------------------

    competency_unit_count = fields.Integer(
        string="No. of competences",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help="Number of active competence standards linked to this line",
        compute="_compute_competency_unit_count",
        store=True,
        copy=False,
    )

    @api.depends(
        "competency_unit_ids",
        "competency_unit_ids.active",
    )
    def _compute_competency_unit_count(self):
        counts = many2many_count(
            self,
            "competency_unit_ids",
        )

        for record in self:
            record.competency_unit_count = counts.get(record.id, 0)

    is_section = fields.Boolean(
        string="Is section",
        required=False,
        readonly=False,
        index=True,
        default=False,
        help="If checked, this record is a visual section/separator",
        copy=True,
    )

    @api.onchange("is_section")
    def _onchange_is_section(self):
        if self.is_section:
            self.training_module_id = None

    needs_synchronization = fields.Boolean(
        string="Para sincronizar",
        required=False,
        readonly=True,
        index=True,
        default=True,
        help="True if the line has changed since the last time it was "
        "sychronized.",
        copy=False,
    )

    # -- Constraints ----------------------------------------------------------

    _sql_constraints = [  # noqa: RUF012
        (
            "code_unique",
            "UNIQUE(code)",
            "Program line code must be unique",
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

    @api.constrains("training_program_id")
    def _check_training_program_type(self):
        """Prevent adding lines to training support programs.

        Raises:
            ValidationError: If a program line belongs to a training support
                program.
        """
        err_msg = _("A Training Support Program cannot have training lines.")

        for record in self:
            if record.training_program_id.program_type == "support":
                raise ValidationError(err_msg)

    @api.constrains("is_section", "training_module_id")
    def _check_training_module(self):
        """Ensure the module matches the program line type.

        Raises:
            ValidationError: If a section has a training module or a regular
                program line has no training module.
        """
        section_msg = _("A section cannot have a training module.")
        line_msg = _("A training module is required for a program line.")

        for record in self:
            if record.is_section and record.training_module_id:
                raise ValidationError(section_msg)

            if not record.is_section and not record.training_module_id:
                raise ValidationError(line_msg)

    # -- Methods overrides ----------------------------------------------------

    @api.model_create_multi
    def create(self, values_list):
        for values in values_list:
            values.setdefault("code", uuid4().hex[:8])

        sanitize_code(values_list, "upper")
        return super().create(values_list)

    def write(self, values):
        sanitize_code(values, "upper")

        if any(key in self._SYNCHRONIZATION_KEYS for key in values):
            values["needs_synchronization"] = True

        return super().write(values)

    def copy(self, default=None):
        """Duplicate the program line into another training program.

        Args:
            default (dict | None): Values to override on the duplicated line.
                The target program can be supplied through
                ``training_program_id``. Defaults to None.

        Returns:
            academy.training.program.line: Newly created program line.

        Raises:
            ValidationError: If no target training program is provided or if
                the target is the current training program.
        """
        self.ensure_one()

        default = dict(default or {})

        if self._name == "academy.training.program.line":
            self._ensure_new_training_program_on_copy(default)

        if "code" not in default:
            default["code"] = uuid4().hex[:8]

        return super().copy(default)

    # -- Public methods -------------------------------------------------------

    def view_current_record(self):
        self.ensure_one()

        action_xid = "academy_base.action_training_program_line_act_window"
        act_wnd = self.env.ref(action_xid)

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": act_wnd.res_model,
            "target": "current",
            "name": self.name,
            "view_mode": "form",
            "domain": [],
            "context": context,
            "search_view_id": act_wnd.search_view_id.id,
            "help": act_wnd.help,
            "res_id": self.id,
            "views": [(False, "form")],
        }

        return serialized

    # -- Auxiliary methods ----------------------------------------------------

    def _ensure_new_training_program_on_copy(self, default):
        """Ensure a different target program is used when duplicating a line.

        Args:
            default (dict): Values that will be passed to ``copy``.

        Returns:
            None

        Raises:
            ValidationError: If no target program is supplied or if it is the
                same program as the source line.
        """
        program_id = default.get("training_program_id")

        if isinstance(program_id, models.BaseModel):
            program_id.ensure_one()
            program_id = program_id.id

        if not program_id:
            program_id = self.env.context.get("default_training_program_id")

        if isinstance(program_id, models.BaseModel):
            program_id.ensure_one()
            program_id = program_id.id

        if not program_id:
            raise ValidationError(
                _(
                    "A training program is required to duplicate this line. "
                    "Provide it via context as 'default_training_program_id' "
                    "or in defaults as 'training_program_id'."
                )
            )

        if program_id == self.training_program_id.id:
            raise ValidationError(
                _(
                    "Cannot duplicate into the same training program. "
                    "Please choose a different target program."
                )
            )

        default["training_program_id"] = program_id
