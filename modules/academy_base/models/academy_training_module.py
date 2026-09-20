###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################


from logging import getLogger
from uuid import uuid4

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval
from odoo.tools.translate import _

from ..utils.helpers import (
    default_code,
    many2many_count,
    one2many_count,
    one2many_count_search_domain,
    sanitize_code,
)

MODULE_SEQUENCE = "academy.training.module.sequence"
UNIT_SEQUENCE = "academy.training.unit.sequence"

_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyTrainingModule(models.Model):
    """A module is a piece of training which can be can be used in serveral
    training activities at the same time
    """

    _name = "academy.training.module"
    _description = "Academy training module"

    _inherit = [  # noqa: RUF012
        "ownership.mixin",
        "image.mixin",
        "mail.thread",
    ]

    _rec_name = "name"
    _order = "parent_path, sequence, name"
    _rec_names_search = ["name", "code"]  # noqa: RUF012

    _parent_name = "training_module_id"
    _parent_store = True

    # ---------------------------- ENTITY FIELDS ------------------------------

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Enter new name",
        size=1024,
        translate=True,
        copy=False,
        tracking=True,
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Enter new description",
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

    training_module_id = fields.Many2one(
        string="Training module",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Parent module",
        comodel_name="academy.training.module",
        domain=[("training_module_id", "=", False)],
        context={},
        ondelete="cascade",
        auto_join=False,
        copy=False,
        tracking=True,
    )

    training_unit_ids = fields.One2many(
        string="Training units",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Training units in this module",
        comodel_name="academy.training.module",
        inverse_name="training_module_id",
        domain=[],
        context={},
        auto_join=False,
        copy=False,
    )

    parent_path = fields.Char(
        string="Parent path",
        required=False,
        readonly=True,
        index=True,
        default=False,
        help="Technical path used to speed up 'child_of' domain lookups.",
        copy=False,
    )

    code = fields.Char(
        string="Code",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_code(),
        help="Enter module code",
        size=30,
        translate=False,
        copy=False,
        tracking=True,
    )

    def default_code(self):
        if self.env.context.get("default_training_module_id", False):
            return default_code(self.env, UNIT_SEQUENCE)

        return default_code(self.env, MODULE_SEQUENCE)

    hours = fields.Float(
        string="Hours",
        required=True,
        readonly=False,
        index=False,
        default=0.0,
        digits=(16, 2),
        help="Length in hours",
        copy=True,
        tracking=True,
    )

    sequence = fields.Integer(
        string="Sequence",
        required=False,
        readonly=False,
        index=False,
        default=0,
        help="Choose the unit order",
        copy=True,
    )

    program_line_ids = fields.One2many(
        string="Program lines",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=False,
        comodel_name="academy.training.program.line",
        inverse_name="training_module_id",
        domain=[],
        context={},
        auto_join=False,
        copy=False,
    )

    program_line_count = fields.Integer(
        string="No. of lines",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help=False,
        compute="_compute_program_line_count",
        search="_search_program_line_count",
        copy=False,
    )

    @api.depends("program_line_ids")
    def _compute_program_line_count(self):
        counts = one2many_count(self, "program_line_ids")

        for record in self:
            record.program_line_count = counts.get(record.id, 0)

    @api.model
    def _search_program_line_count(self, operator, value):
        return one2many_count_search_domain(
            self,
            "program_line_ids",
            operator,
            value,
        )

    # --------------------------- COMPUTED FIELDS -----------------------------

    training_unit_count = fields.Integer(
        string="No. of units",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help="Show the number of training units in the training module",
        compute="_compute_training_unit_count",
        search="_search_training_unit_count",
        copy=False,
    )

    @api.depends("training_unit_ids")
    def _compute_training_unit_count(self):
        counts = one2many_count(self, "training_unit_ids")

        for record in self:
            record.training_unit_count = counts.get(record.id, 0)

    @api.model
    def _search_training_unit_count(self, operator, value):
        return one2many_count_search_domain(
            self,
            "training_unit_ids",
            operator,
            value,
        )

    delivered_modules_ids = fields.Many2many(
        string="Deliverable modules",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help=(
            "If the module has no children, it points to itself. "
            "If it has children, it points to its sub-modules."
        ),
        comodel_name="academy.training.module",
        compute="_compute_delivered_modules_ids",
        copy=False,
    )

    @api.depends("training_unit_ids")
    def _compute_delivered_modules_ids(self):
        for record in self:
            if record.training_unit_ids:
                record.delivered_modules_ids = record.training_unit_ids
            else:
                record.delivered_modules_ids = record

    training_program_ids = fields.Many2many(
        string="Training programs",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Training programs that use this training module",
        comodel_name="academy.training.program",
        relation="academy_training_module_training_program_rel",
        column1="training_module_id",
        column2="training_program_id",
        domain=[],
        context={},
        compute="_compute_training_program_ids",
        store=True,
        copy=False,
    )

    @api.depends(
        "program_line_ids",
        "program_line_ids.active",
        "program_line_ids.training_program_id",
    )
    def _compute_training_program_ids(self):
        program_ids_by_module = {
            record.id: set() for record in self if record.id
        }

        line_obj = self.env["academy.training.program.line"]

        rows = line_obj.read_group(
            domain=[
                ("training_module_id", "in", self.ids),
                ("active", "=", True),
            ],
            fields=[
                "training_module_id",
                "training_program_id",
            ],
            groupby=[
                "training_module_id",
                "training_program_id",
            ],
            lazy=False,
        )

        for row in rows:
            module = row.get("training_module_id")
            program = row.get("training_program_id")

            if module and program:
                program_ids_by_module[module[0]].add(program[0])

        program_obj = self.env["academy.training.program"]

        for record in self:
            program_ids = program_ids_by_module.get(record.id, set())
            record.training_program_ids = program_obj.browse(program_ids)

    training_program_count = fields.Integer(
        string="No. of programs",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help="Number of training programs using this training module",
        compute="_compute_training_program_count",
        store=True,
        copy=False,
    )

    @api.depends("training_program_ids")
    def _compute_training_program_count(self):
        counts = many2many_count(self, "training_program_ids")

        for record in self:
            record.training_program_count = counts.get(record.id, 0)

    # --- SQL constraints --------------------------------------------------

    _sql_constraints = [  # noqa: RUF012
        (
            "code_unique",
            "unique(code)",
            "Module code must be unique",
        ),
        (
            "hours_non_negative",
            "CHECK(hours >= 0)",
            "Hours must be a non-negative number",
        ),
    ]

    @api.constrains("training_module_id", "training_unit_ids")
    def _check_two_level_hierarchy(self):
        """Enforce a two-level hierarchy and prevent cycles:
        - A unit (has training_module_id) cannot have subunits.
        - Only top-level modules (without parent) can be selected as parent.
        - No cyclic parent chains.
        """
        for record in self:
            # 1) A unit cannot have subunits
            if record.training_module_id and record.training_unit_ids:
                raise ValidationError(
                    _("A training unit cannot have subunits.")
                )

            # 2) Only top-level modules can be selected as parent
            parent = record.training_module_id
            if parent and parent.training_module_id:
                raise ValidationError(
                    _("Only top-level modules can be selected as parent.")
                )

    @api.constrains("training_module_id")
    def _check_no_cycles(self):
        message = _("Cyclic hierarchy is not allowed.")
        for record in self:
            if record._has_cycle(field_name="training_module_id"):
                raise ValidationError(message)

    # -- Methods overrides ----------------------------------------------------

    @api.model_create_multi
    def create(self, values_list):
        sanitize_code(values_list, "upper")

        result = super().create(values_list)
        after_parents = result.mapped("training_module_id")

        self._update_parent_hours(parents=after_parents)

        return result

    def write(self, values):
        sanitize_code(values, "upper")

        before_parents = self.mapped("training_module_id")
        result = super().write(values)
        after_parents = self.mapped("training_module_id")

        affected = before_parents | after_parents
        self._update_parent_hours(parents=affected)

        return result

    def unlink(self):
        parents = self.mapped("training_module_id")

        result = super().unlink()

        self.env["academy.training.module"]._update_parent_hours(
            parents=parents
        )

        return result

    def copy(self, default=None):
        self.ensure_one()

        default = dict(default or {})

        self._prevent_copy_training_units(default)

        if not default.get("name"):
            name = self.name or _("New training module")
            suffix = uuid4().hex[:8]
            default["name"] = f"{name} ‒ {suffix}"

        new_module = super().copy(default)

        unit_default = {
            "training_module_id": new_module.id,
        }

        for unit in self.training_unit_ids:
            unit.with_context(default_training_module_id=new_module.id).copy(
                default=unit_default
            )

        return new_module

    # -------------------------- PUBLIC METHODS -------------------------------

    def view_training_units(self):
        self.ensure_one()

        name = self.env._("Units/Blocks: {}").format(self.display_name)

        action_xid = "academy_base.action_training_module_units_act_window"
        act_wnd = self.env.ref(action_xid)

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))
        context.update({"default_training_module_id": self.id})

        domain = [("training_module_id", "=", self.id)]

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
            "path": act_wnd.path,
        }

        if act_wnd.view_ids:
            serialized["views"] = [
                (v.view_id.id, v.view_mode) for v in act_wnd.view_ids
            ]

        return serialized

    def view_training_program_lines(self):
        self.ensure_one()

        name = self.env._("Program: {}").format(self.display_name)

        action_xid = "academy_base.action_training_program_line_act_window"
        act_wnd = self.env.ref(action_xid)

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))
        context.update({"default_training_module_id": self.id})

        domain = [("training_module_id", "=", self.id)]

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

    def view_training_programs(self):
        self.ensure_one()

        name = self.env._("Programs: {}").format(self.display_name)

        action_xid = "academy_base.action_academy_training_program_act_window"
        act_wnd = self.env.ref(action_xid)

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))

        domain = [("id", "in", self.training_program_ids.ids)]

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

    # -------------------------- AUXILIARY METHODS ----------------------------

    def _prevent_copy_training_units(self, default):
        parent_id = self.training_module_id.id or False
        new_parent_id = default.get("training_module_id", False)

        if isinstance(new_parent_id, models.BaseModel):
            new_parent_id.ensure_one()
            new_parent_id = new_parent_id.id

        if parent_id and (not new_parent_id or parent_id == new_parent_id):
            raise UserError(
                _("Duplicating training units/blocks is strictly prohibited.")
            )

    def _get_id(self, model_or_id):
        """Return the identifier represented by an ID or singleton recordset."""
        if isinstance(model_or_id, models.BaseModel):
            model_or_id.ensure_one()
            return model_or_id.id

        return model_or_id

    @api.model
    def _update_parent_hours(self, parents=None):
        """Recompute total hours for the supplied parent modules.

        The total is calculated from active child units. Parents without active
        children are explicitly reset to zero.

        Args:
            parents (recordset[academy.training.module] | None): Parent modules
                whose total hours must be recomputed.

        Returns:
            None
        """
        if not parents:
            return

        parents = parents.exists()
        if not parents:
            return

        totals = dict.fromkeys(parents.ids, 0.0)

        rows = self.read_group(
            domain=[
                ("training_module_id", "in", parents.ids),
                ("active", "=", True),
            ],
            fields=["hours:sum"],
            groupby=["training_module_id"],
        )

        for row in rows:
            parent_id = row["training_module_id"][0]
            totals[parent_id] = row.get("hours", 0.0)

        for parent in parents:
            total_hours = totals[parent.id]

            if parent.hours != total_hours:
                parent.write({"hours": total_hours})
