# -*- coding: utf-8 -*-
""" AcademyTrainingProgram

This module contains the academy.training.program Odoo model which stores
all training program attributes and behavior.
"""


# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.osv.expression import TRUE_DOMAIN, FALSE_DOMAIN
from odoo.exceptions import ValidationError
from ..utils.helpers import OPERATOR_MAP, one2many_count
from ..utils.helpers import sanitize_code, default_code
from odoo.tools.safe_eval import safe_eval
from odoo.tools.translate import _

from logging import getLogger
from uuid import uuid4

CODE_SEQUENCE = "academy.training.program.sequence"

_logger = getLogger(__name__)


class AcademyTrainingProgram(models.Model):
    """This describes the program offered, its modules and training units"""

    _name = "academy.training.program"
    _description = "Academy training program"

    _inherit = [
        "ownership.mixin",
        "image.mixin",
        "mail.thread",
        "mail.activity.mixin",
    ]

    _rec_name = "name"
    _order = "name ASC"
    _rec_names_search = ["name", "code", "training_framework_id"]

    _IMMUTABLE_FIELDS = ("program_type", "training_framework_id")

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Official name of the training program",
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
        help="Detailed description of the Training Program",
        translate=True,
        copy=True,
    )

    active = fields.Boolean(
        string="Active",
        required=False,
        readonly=False,
        index=False,
        default=True,
        help="Disable to archive without deleting",
        copy=True,
        tracking=True,
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

    code = fields.Char(
        string="Code",
        required=True,
        readonly=False,
        index=True,
        default=lambda self: default_code(self.env, CODE_SEQUENCE),
        help="Public code or short identifier for the program",
        size=30,
        translate=False,
        copy=False,
        tracking=True,
    )

    # Field program_type and onchange -----------------------------------------

    program_type = fields.Selection(
        string="Program type",
        required=True,
        readonly=True,
        index=True,
        default="training",
        help="Select whether this is a standard training program or a "
        "training support program.",
        selection=[
            ("training", "Training Program"),
            ("support", "Training Support Program"),
        ],
    )

    @api.onchange("program_type")
    def _onchange_program_type_clear_lines(self):
        if self.program_type == "support":
            self.program_line_ids = [(5, 0, 0)]

    training_framework_id = fields.Many2one(
        string="Training framework",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Training framework to which this program belongs",
        comodel_name="academy.training.framework",
        domain=[],
        context={},
        ondelete="restrict",
        auto_join=False,
        copy=True,
        tracking=True,
    )

    professional_family_id = fields.Many2one(
        string="Professional family",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Professional family to which this program belongs",
        comodel_name="academy.professional.family",
        domain=[],
        context={},
        ondelete="set null",
        auto_join=False,
        copy=True,
    )

    @api.onchange("professional_family_id")
    def _onchange_professional_family_id(self):
        self.professional_area_id = None

    professional_area_id = fields.Many2one(
        string="Professional area",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Professional area to which this program belongs",
        comodel_name="academy.professional.area",
        domain=[],
        context={},
        ondelete="set null",
        auto_join=False,
        copy=True,
    )

    professional_field_id = fields.Many2one(
        string="Professional field",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Professional field associated with this program",
        comodel_name="academy.professional.field",
        domain=[],
        context={},
        ondelete="set null",
        auto_join=False,
        copy=True,
    )

    @api.onchange("professional_field_id")
    def _onchange_professional_field_id(self):
        self.professional_sector_ids = [(5, 0, 0)]

    professional_sector_ids = fields.Many2many(
        string="Professional sectors",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Professional sectors related to this program",
        comodel_name="academy.professional.sector",
        relation="academy_training_program_professional_sector_rel",
        column1="training_program_id",
        column2="professional_sector_id",
        domain=[],
        context={},
        copy=True,
    )

    qualification_level_id = fields.Many2one(
        string="Qualification level",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Qualification level to which this training program belongs",
        comodel_name="academy.qualification.level",
        domain=[],
        context={},
        ondelete="set null",
        auto_join=False,
        copy=True,
    )

    attainment_id = fields.Many2one(
        string="Educational attainment",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Minimum educational requirement to access this program",
        comodel_name="academy.educational.attainment",
        domain=[],
        context={},
        ondelete="set null",
        auto_join=False,
        copy=True,
    )

    general_competence = fields.Text(
        string="General competence",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Overall competence expected after completing the program",
        translate=True,
        copy=True,
    )

    program_line_ids = fields.One2many(
        string="Program lines",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Program lines (modules) included in this program",
        comodel_name="academy.training.program.line",
        inverse_name="training_program_id",
        domain=[],
        context={},
        auto_join=False,
        copy=False,
    )

    # Computed field: program_line_count --------------------------------------

    program_line_count = fields.Integer(
        string="No. of lines",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help="Computed number of program lines",
        compute="_compute_program_line_count",
        store=True,
        copy=False,
    )

    @api.depends("program_line_ids")
    def _compute_program_line_count(self):
        domain = [("is_section", "=", False)]
        counts = one2many_count(self, "program_line_ids", domain)

        for record in self:
            record.program_line_count = counts.get(record.id, 0)

    training_action_ids = fields.One2many(
        string="Training actions",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Training actions (editions) that use this program",
        comodel_name="academy.training.action",
        inverse_name="training_program_id",
        domain=[],
        context={},
        auto_join=False,
        check_company=True,
        copy=False,
    )

    # Computed field: training_action_count -----------------------------------

    training_action_count = fields.Integer(
        string="No. of actions",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help="Computed number of training actions",
        compute="_compute_training_action_count",
        search="_search_training_action_count",
        copy=False,
    )

    @api.depends("training_action_ids")
    def _compute_training_action_count(self):
        counts = one2many_count(self, "training_action_ids")

        for record in self:
            record.training_action_count = counts.get(record.id, 0)

    @api.model
    def _search_training_action_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = one2many_count(self.search([]), "training_action_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    # Computed field: hours --------------------------------------------------

    hours = fields.Float(
        string="Hours",
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help="Total hours computed from linked modules",
        compute="_compute_hours",
        store=True,
        copy=True,
        tracking=True,
    )

    @api.depends("program_line_ids.training_module_id.hours")
    def _compute_hours(self):
        hours_path = "program_line_ids.training_module_id.hours"
        for record in self:
            hours_list = record.mapped(hours_path)
            record.hours = sum(hours_list) if hours_list else 0.0

    # -------------------------- Contraints -----------------------------------

    _sql_constraints = [
        (
            "code_unique",
            "unique(code)",
            "Program code must be unique",
        ),
    ]

    @api.constrains("program_type", "program_line_ids")
    def _check_support_program_has_no_lines(self):
        """A Training Support Program cannot have training lines."""
        for rec in self:
            if rec.program_type == "support" and rec.program_line_ids:
                raise ValidationError(
                    _("A Training Support Program cannot have training lines.")
                )

    # ---------------------------- PUBLIC FIELDS ------------------------------

    def update_from_external(self, crud, fieldname, recordset):
        """Observer notify method, will be called by action"""
        self._compute_training_action_count()

    def view_training_actions(self):
        self.ensure_one()

        name = self.env._("Actions: {}").format(self.display_name)

        action_xid = "academy_base.action_training_action_act_window"
        act_wnd = self.env.ref(action_xid)

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))
        context.update({"default_training_program_id": self.id})

        domain = [("training_program_id", "=", self.id)]

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

    def view_training_program_lines(self):
        self.ensure_one()

        name = self.env._("Program: {}").format(self.display_name)

        action_xid = "academy_base.action_training_program_line_act_window"
        act_wnd = self.env.ref(action_xid)

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))
        context.update({"default_training_program_id": self.id})

        domain = [("training_program_id", "=", self.id)]

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

    # -- Methods overrides ----------------------------------------------------

    @api.model_create_multi
    def create(self, values_list):
        sanitize_code(values_list, "upper")
        return super().create(values_list)

    def write(self, values):
        """Overridden method 'write'"""
        values = values or {}

        self._avoid_writing_to_immutable_fields(values)
        sanitize_code(values, "upper")

        return super().write(values)

    def copy(self, default=None):
        self.ensure_one()

        default = dict(default or {})

        if not default.get("name", False):
            name = self.name or _("New training program")
            sufix = uuid4().hex[:8]
            default["name"] = f"{name} ‒ {sufix}"

        new_program = super().copy(default)

        line_default = {"training_program_id": new_program.id}
        for line in self.program_line_ids:
            line.copy(default=line_default)

        return new_program

    def _avoid_writing_to_immutable_field(self, values, field_name):
        self.ensure_one()

        field = self._fields[field_name]
        new = values.get(field_name)
        # Normalizar Many2one a ID para comparar
        if field.type == "many2one":
            old = self[field_name].id or False
            if isinstance(new, models.BaseModel):
                new = new.id
        else:
            old = self[field_name]
        if new != old:
            raise ValidationError(
                _("Field '%s' cannot be modified after saving.") % field.string
            )

    def _avoid_writing_to_immutable_fields(self, values):
        fields_to_check = set(values) & set(self._IMMUTABLE_FIELDS)
        if fields_to_check:
            for record in self:
                for field_name in fields_to_check:
                    record._avoid_writing_to_immutable_field(
                        values, field_name
                    )

        return True

    # -- Method: synchronize_training_actions and auxiliary logic
    # -------------------------------------------------------------------------

    def synchronize_training_actions(self, **kwargs):
        """
        Synchronize training program lines into their related training actions.

        This routine overwrites existing action lines to mirror program lines,
        creates missing ones, optionally removes orphans, and posts one short
        note in the chatter of each affected training action.

        Workflow
        --------
        1) Scope target actions for these programs (optionally only top-level).
        2) Compute shared fields to sync (chatter/technical fields excluded).
        3) For each program line:
           - Build a write-format dict from the program line.
           - Overwrite all matching action lines (tracking disabled).
           - If allowed, stage create-values for missing lines.
        4) Bulk-create missing action lines (tracking disabled).
        5) Optionally unlink action lines with no matching program line.
        6) Post a single sync note per affected training action.

        Parameters (kwargs)
        -------------------
        optional : bool, default True
            If False, skip creation of optional lines; existing ones are still
            overwritten.
        remove_mismatches : bool, default True
            If True, delete action lines whose program_line_id is empty or
            outside the current program.
        synchronize_groups : bool, default True
            If False, limit scope to root actions only (parent_id = False). If
            True, include all actions (roots and children).
        target_set : recordset | int | Iterable[int], optional
            Further restrict actions to process. Accepts an action recordset, a
            single ID, or a list/tuple of IDs.

        Side effects
        ------------
        - Writes/creates on academy.training.action.line (tracking disabled).
        - May unlink academy.training.action.line records.
        - Posts a note (subtype mail.mt_note) on each affected action.

        Notes
        -----
        - Overwrite-first design: no per-field delta check.
        - No defensive de-duplication on create; uniqueness errors surface so
          data issues can be fixed.

        Returns
        -------
        recordset
            academy.training.action.line records that were created or
            overwritten.
        """
        kwargs = kwargs or {}

        _logger.info(
            "Synchronization started: training programs → training actions."
        )

        # 1) Parse kwargs and set defaults
        optional = kwargs.get("optional", True)
        remove_mismatches = kwargs.get("remove_mismatches", True)
        synchronize_groups = kwargs.get("synchronize_groups", True)
        target_set = self._sta_get_target_set(**kwargs)

        # 2) Find training actions for these programs
        action_set = self._sta_get_actions(target_set, synchronize_groups)
        grouped_act_set = self._sta_group_by_program(action_set)

        # 3) Fetch program lines; index action lines by program line
        shared_keys = self._sta_get_shared_keys()
        program_set = self or action_set.mapped("training_program_id")
        prog_line_set = program_set.mapped("program_line_ids")
        act_line_set = action_set.mapped("action_line_ids")
        grouped_act_lines = self._sta_group_by_program_line(act_line_set)

        # 4) For each program line, sync related action lines
        act_line_obj = self.env["academy.training.action.line"]
        empty_act_line = act_line_obj.browse()
        result_set = act_line_obj.browse()
        creation_value_list = []
        for prog_line in prog_line_set:
            values = self._sta_read_source_values(prog_line, shared_keys)

            # 5) Update existing lines (even if optional)
            update_set = grouped_act_lines.get(prog_line.id, empty_act_line)
            result_set |= self._sta_update_lines(
                update_set, values, shared_keys
            )

            # 6) Skip creation for optional lines (optional=False)
            if prog_line.optional and not optional:
                continue

            # 7.a) Compute missing actions and build create values
            create_over_set = self._sta_compute_create_over(
                prog_line, grouped_act_set, update_set
            )
            values_list = self._sta_create_values(create_over_set, values)
            if values_list:
                creation_value_list.extend(values_list)

        # 7.b) Create missing lines (bulk)
        result_set |= self._sta_create_lines(creation_value_list)

        # 8) Remove action lines without a matching program line
        act_line_set = action_set.mapped("action_line_ids")  # After upsert
        self._sta_unlink(prog_line_set, act_line_set, remove_mismatches)

        # 9) Chatter note on all lines touched (created or overwritten)
        self._notify_synchronization(result_set)

        _logger.info(
            "Synchronization finished: training programs → training actions."
        )

        return result_set

    def _sta_get_target_set(self, **kwargs):
        value = kwargs.get("target_set", False)
        action_obj = self.env["academy.training.action"]

        if not value:
            target_set = action_obj.browse()
        elif isinstance(value, models.Model):
            if value._name == "academy.training.action":
                target_set = value
            else:
                target_set = action_obj.browse()
        elif isinstance(value, int):
            target_set = action_obj.browse(value)
        elif isinstance(value, (list, tuple)):
            ids = [v for v in value if isinstance(v, int)]
            target_set = action_obj.browse(ids) if ids else action_obj.browse()
        else:
            target_set = action_obj.browse()

        return target_set

    def _sta_get_actions(self, target_set, synchronize_groups):
        """
        Return the training actions to synchronize.

        Selection rules:
          - self & target_set → intersection.
          - only self         → actions of those programs.
          - only target_set   → exactly those actions.
          - neither           → empty recordset.
        """
        action_obj = self.env["academy.training.action"]

        if not self and not target_set:
            actions = action_obj.browse()
        else:
            domain = []

            if self:
                self_leaf = ("training_program_id", "in", self.ids)
                domain.append(self_leaf)

            if target_set:
                target_leaf = ("id", "in", target_set.ids)
                domain.append(target_leaf)

            if not synchronize_groups:
                parent_leaf = ("parent_id", "=", False)
                domain.append(parent_leaf)

            actions = action_obj.search(domain)
            print(actions)

        _logger.debug(
            "Synchronization scope: %d training action(s) selected.",
            len(actions),
        )

        return actions

    @staticmethod
    def _sta_group_by_program(action_set):
        grouped_by_program = {}

        for action in action_set:
            program = action.training_program_id
            if not program:
                continue
            program_id = program.id
            if program_id not in grouped_by_program:
                grouped_by_program[program_id] = action
            else:
                grouped_by_program[program_id] |= action

        return grouped_by_program

    @staticmethod
    def _sta_group_by_program_line(action_line_set):
        grouped_by_program = {}

        for action_line in action_line_set:
            prog_line_id = action_line.program_line_id.id
            if not prog_line_id:
                continue

            if prog_line_id not in grouped_by_program:
                grouped_by_program[prog_line_id] = action_line
            else:
                grouped_by_program[prog_line_id] |= action_line

        return grouped_by_program

    @staticmethod
    def _sta_unlink(prog_lines, act_lines, remove_mismatches):
        if not remove_mismatches:
            return

        prog_line_ids = prog_lines.ids
        to_unlink = act_lines.filtered(
            lambda line: not line.program_line_id
            or line.program_line_id.id not in prog_line_ids
        )

        _logger.debug(
            "Synchronization cleanup: will remove %d unmatched action "
            "line(s).",
            len(to_unlink),
        )

        if to_unlink:
            to_unlink.unlink()

    def _sta_get_shared_keys(self):
        prog_line_obj = self.env["academy.training.program.line"]
        shared_keys = set(prog_line_obj._fields)

        act_line_obj = self.env["academy.training.action.line"]
        shared_keys &= set(act_line_obj._fields)

        shared_keys.discard("comment")

        mail_thread_obj = self.env["mail.thread"]
        shared_keys -= set(mail_thread_obj._fields)

        _logger.debug(
            "Synchronization fields: %s",
            ", ".join(sorted(map(str, shared_keys))),
        )

        return shared_keys

    @staticmethod
    def _sta_read_source_values(program_line, shared_keys):
        raw = {k: program_line[k] for k in shared_keys}
        values = program_line._convert_to_write(raw)

        values["program_line_id"] = program_line.id

        return values

    @api.model
    def _sta_compute_create_over(
        self, program_line, grouped_actions, updated_action_lines
    ):
        program_id = program_line.training_program_id.id
        related_action_set = grouped_actions.get(
            program_id, self.env["academy.training.action"].browse()
        )

        updated_action_set = updated_action_lines.mapped("training_action_id")

        return related_action_set - updated_action_set

    def _sta_update_lines(self, act_line_set, values, shared_keys):
        """Actualiza únicamente las líneas cuyo estado difiere de `values`
        (write-dict).
        """
        if not act_line_set:
            return act_line_set

        _logger.debug(
            "Synchronization updates: %d action line(s) will be overwritten.",
            len(act_line_set),
        )
        vals2write = dict(values)
        # Blindaje: nunca mover líneas entre acciones en updates
        vals2write.pop("training_action_id", None)
        # Reducir ruido de chatter/seguimiento
        context = dict(tracking_disable=True, mail_create_nosubscribe=True)
        act_line_set.with_context(context).write(vals2write)

        return act_line_set

    @staticmethod
    def _sta_create_values(create_over_set, base_values):
        values = dict(base_values)
        creation_value_list = []

        for action in create_over_set:
            creation_values = values.copy()
            creation_values["training_action_id"] = action.id
            creation_value_list.append(creation_values)

        return creation_value_list

    def _sta_create_lines(self, creation_value_list):
        _logger.debug(
            "Synchronization inserts: %d action line(s) will be created.",
            len(creation_value_list),
        )

        act_line_obj = self.env["academy.training.action.line"]
        if creation_value_list:
            context = dict(tracking_disable=True, mail_create_nosubscribe=True)
            act_line_ctx = act_line_obj.with_context(context)
            result_set = act_line_ctx.create(creation_value_list)
        else:
            result_set = act_line_obj.browse()

        return result_set

    @api.model
    def _notify_synchronization(self, result_set):
        """Post one short sync note on each affected training action."""
        action_obj = self.env["academy.training.action"]
        if not result_set:
            return action_obj.browse()

        action_set = result_set.mapped("training_action_id")
        if not action_set:
            return action_obj.browse()

        # Silenciar tracking/seguidores/notificaciones por email
        ctx = {
            "tracking_disable": True,
            "mail_notrack": True,
            "mail_create_nosubscribe": True,
            "mail_post_autofollow": False,
            "mail_notify_force_send": False,
        }
        body = self.env._(
            "Synchronization: this training action was synchronized from "
            "its training program."
        )

        for action in action_set.with_context(**ctx):
            action.message_post(
                body=body,
                message_type="comment",
                subtype_xmlid="mail.mt_note",
            )

        _logger.debug(
            "Synchronization chatter: posted sync note on %d action(s).",
            len(action_set),
        )
        return action_set
