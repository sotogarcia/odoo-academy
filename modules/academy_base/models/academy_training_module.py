# -*- coding: utf-8 -*-
""" AcademyTrainingModule

This module contains the academy.training.module Odoo model which stores
all training module attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError
from odoo.osv.expression import TRUE_DOMAIN, FALSE_DOMAIN
from ..utils.helpers import OPERATOR_MAP, one2many_count, many2many_count
from ..utils.helpers import sanitize_code, default_code

from logging import getLogger

CODE_SEQUENCE = "academy.training.module.sequence"

_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyTrainingModule(models.Model):
    """A module is a piece of training which can be can be used in serveral
    training activities at the same time
    """

    _name = "academy.training.module"
    _description = "Academy training module"

    _inherit = [
        "image.mixin",
        "mail.thread",
        "ownership.mixin",
    ]

    _rec_name = "name"
    _order = "parent_path, sequence, name"
    _rec_names_search = ["name", "code"]

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
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Enter new description",
        translate=True,
    )

    active = fields.Boolean(
        string="Active",
        required=False,
        readonly=False,
        index=False,
        default=True,
        help="Disable to archive without deleting.",
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
    )

    parent_path = fields.Char(
        string="Parent path",
        required=False,
        readonly=True,
        index=True,
        default=False,
        help="Technical path used to speed up 'child_of' domain lookups.",
    )

    code = fields.Char(
        string="Code",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: default_code(self.env, CODE_SEQUENCE),
        help="Enter code for training module",
        size=30,
        translate=False,
    )

    hours = fields.Float(
        string="Hours",
        required=True,
        readonly=False,
        index=False,
        default=0.0,
        digits=(16, 2),
        help="Length in hours",
    )

    sequence = fields.Integer(
        string="Sequence",
        required=False,
        readonly=False,
        index=False,
        default=0,
        help="Choose the unit order",
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
    )

    program_line_count = fields.Integer(
        string="Program line count",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help=False,
        compute="_compute_program_line_count",
        search="_search_program_line_count",
    )

    @api.depends("program_line_ids")
    def _compute_program_line_count(self):
        counts = one2many_count(self, "program_line_ids")

        for record in self:
            record.program_line_count = counts.get(record.id, 0)

    @api.model
    def _search_program_line_count(self, operator, value):
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = many2many_count(self.search([]), "program_line_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    # --------------------------- COMPUTED FIELDS -----------------------------

    training_unit_count = fields.Integer(
        string="Units",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help="Show the number of training units in the training module",
        compute="_compute_training_unit_count",
        search="_search_training_unit_count",
    )

    @api.depends("training_unit_ids")
    def _compute_training_unit_count(self):
        counts = one2many_count(self, "training_unit_ids")

        for record in self:
            record.training_unit_count = counts.get(record.id, 0)

    @api.model
    def _search_training_unit_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = one2many_count(self.search([]), "training_unit_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    resolved_ids = fields.Many2many(
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
        compute="_compute_resolved_ids",
    )

    @api.depends("training_unit_ids")
    def _compute_resolved_ids(self):
        for record in self:
            if record.training_unit_ids:
                record.resolved_ids = record.training_unit_ids
            else:
                record.resolved_ids = record

    training_program_ids = fields.Many2many(
        string="Training programs",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name="academy.training.program",
        relation="academy_training_module_training_program_rel",
        column1="training_module_id",
        column2="training_program_id",
        domain=[],
        context={},
    )

    training_program_count = fields.Integer(
        string="Training program count",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help="Number of training programs using this training module",
        compute="_compute_training_program_count",
    )

    @api.depends("program_line_ids", "program_line_ids.training_module_id")
    def _compute_training_program_count(self):
        counts = many2many_count(self, "training_program_ids")

        for record in self:
            record.training_program_count = counts.get(record.id, 0)

    # --- SQL constraints --------------------------------------------------

    _sql_constraints = [
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

    def _get_id(self, model_or_id):
        """Returns a valid id or rises an error"""
        if isinstance(model_or_id, int):
            result = model_or_id
        else:
            self.ensure_one()
            result = model_or_id.id

        return result

    @api.model
    def _update_parent_hours(self, parents=None):
        """
        Recompute the 'hours' field for the given parent modules.

        This method sums the 'hours' of all active child modules and updates
        each parent module with the total. It is called after create/write
        operations to keep parent hours consistent with their children.

        Args:
            parents (recordset[academy.training.module] | None):
                Optional recordset of parent modules to update. If None,
                the method will use the parents of the current recordset.

        Returns:
            None
        """
        if not parents:
            return

        module_obj = self.env["academy.training.module"]
        rows = module_obj.read_group(
            domain=[
                ("training_module_id", "in", parents.ids),
                ("active", "=", True),
            ],
            fields=["hours:sum"],
            groupby=["training_module_id"],
        )

        for row in rows:
            training_module_id = row["training_module_id"][0]
            total_hours = row.get("hours", 0.0)

            module = module_obj.browse(training_module_id)
            module.write({"hours": total_hours})
