# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
from ..utils.record_utils import get_active_records, ensure_recordset

from logging import getLogger

_logger = getLogger(__name__)


class AcademyTrainingProgramSynchronizeWizard(models.TransientModel):
    """Synchronize training program with training actions or between parent
    and child training actions.
    """

    _name = "academy.training.program.synchronize.wizard"
    _description = "Academy training program synchronize"

    _rec_name = "id"
    _order = "id DESC"

    source_program_ids = fields.Many2many(
        string="Source programs",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Training programs will be used as the source for "
        "synchronization.",
        comodel_name="academy.training.program",
        relation="academy_training_program_synchronize_wizard_source_rel",
        column1="wizard_id",
        column2="training_program_id",
        domain=[],
        context={},
    )

    source_program_count = fields.Integer(
        string="No. of programs",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help="Total number of source training programs",
        compute="_compute_source_program_count",
    )

    @api.depends("source_program_ids")
    def _compute_source_program_count(self):
        for record in self:
            record.source_program_count = len(record.source_program_ids)

    optional = fields.Boolean(
        string="Include optional",
        required=False,
        readonly=False,
        index=False,
        default=True,
        help="Append optional program lines to target training actions during "
        "synchronization.",
    )

    remove_mismatches = fields.Boolean(
        string="Remove mismatches",
        required=False,
        readonly=False,
        index=False,
        default=True,
        help="Remove target program lines that do not match the source "
        "program.",
    )

    synchronize_groups = fields.Boolean(
        string="Synchronize groups",
        required=False,
        readonly=False,
        index=False,
        default=False,
        help="Also synchronize training groups. If disabled, only parent "
        "training actions will be synchronized.",
    )

    target_action_ids = fields.Many2many(
        string="Target actions",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Training actions will be synchronized with its source program",
        comodel_name="academy.training.action",
        relation="academy_training_program_synchronize_wizard_target_rel",
        column1="wizard_id",
        column2="target_action_id",
        domain=[],
        context={},
    )

    target_action_count = fields.Integer(
        string="No. of actions",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help="Number of given target training actions",
        compute="_compute_target_action_count",
    )

    @api.depends("target_action_ids")
    def _compute_target_action_count(self):
        for record in self:
            record.target_action_count = len(record.target_action_ids)

    @api.model
    def call_wizard(self, **kwargs):
        """Open the wizard and prefill fields from kwargs.

        Keyword Args:
            optional (bool): Preselect appending optional program
                lines. Defaults to False.
            remove_mismatches (bool): Preselect removing target lines that
                are not present in the source program. Defaults to True.
            synchronize_groups (bool): Preselect synchronizing training
                groups in addition to parent actions. Defaults to False.
            source_program_ids (recordset|int|list[int]): Source programs
                (academy.training.program) as a recordset, id or list of ids.
            target_action_ids (recordset|int|list[int]): Target actions
                (academy.training.action) as a recordset, id or list of ids.
            show_dialog (bool): If True, return an act_window to display the
                wizard; if False, return the created wizard record. Defaults
                to True.

        Returns:
            dict | recordset: act_window when show_dialog is True, otherwise
            the created wizard (single-record recordset).
        """

        values = {
            "optional": kwargs.get("optional", False),
            "remove_mismatches": kwargs.get("remove_mismatches", True),
            "synchronize_groups": kwargs.get("synchronize_groups", False),
        }

        field, model = "source_program_ids", "academy.training.program"
        source_programs = self._get_records(kwargs, field, model)
        if source_programs:
            m2m_op = [(6, 0, source_programs.ids)]
            values[field] = m2m_op

        field, model = "target_action_ids", "academy.training.action"
        target_actions = self._get_records(kwargs, field, model)
        if target_actions:
            m2m_op = [(6, 0, target_actions.ids)]
            values[field] = m2m_op

        new_wizard = self.create(values)

        if kwargs.get("show_dialog", True):
            return self.view_wizard(new_wizard)

        return new_wizard

    def view_wizard(self, wizard=None):
        wizard = (wizard and wizard[0]) or self

        action_xid = "{}.{}".format(
            "academy_base",
            "action_academy_training_program_synchronize_wizard_act_window",
        )
        act_wnd = wizard.env.ref(action_xid)

        context = wizard.env.context.copy()
        context.update(safe_eval(act_wnd.context))

        domain = safe_eval(act_wnd.domain)

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": act_wnd.res_model,
            "target": "new",
            "name": act_wnd.name,
            "view_mode": act_wnd.view_mode,
            "domain": domain,
            "context": context,
            "search_view_id": act_wnd.search_view_id.id,
            "help": act_wnd.help,
        }

        if wizard:
            serialized["res_id"] = wizard.id

        return serialized

    def _perform_action(self):
        self.ensure_one()

        return self.synchronize_training_actions(
            optional=self.optional,
            remove_mismatches=self.remove_mismatches,
            synchronize_groups=self.synchronize_groups,
            source_set=self.source_program_ids,
            target_set=self.target_action_ids,
        )

    def perform_action(self):
        result_set = self.env["academy.training.action.line"].browse()

        for record in self:
            result_set |= self._perform_action()

        return result_set

    @api.model
    def _get_records(self, kwargs, key, expected):
        if isinstance(expected, str):
            recordset = self.env[expected]
        else:
            recordset = expected

        assert hasattr(recordset, "_name"), "Invalid argument 'expected'"

        # 1. Try to get from kwargs
        values = kwargs.get(key, False)
        if values:
            recordset = ensure_recordset(self.env, values, recordset._name)

        # 2. Try to get from context
        if not recordset:
            recordset = get_active_records(self.env, recordset._name)

        return recordset

    # -- Method: synchronize_training_actions and auxiliary logic
    # -------------------------------------------------------------------------

    @api.model
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
            If True, delete action lines whose `program_line_id` is empty or
            not part of the current set of program lines being synchronized.
        synchronize_groups : bool, default True
            If False, limit scope to root actions only (`parent_id = False`).
            If True, include all actions (roots and children).
        source_set : recordset | int | Iterable[int], optional
            Set of training programs to sync from. Accepts an
            `academy.training.program` recordset, a single ID, or a list/tuple
            of IDs. If omitted, it is inferred from `target_set` by taking each
            action’s `training_program_id`.
        target_set : recordset | int | Iterable[int], optional
            Actions to process. Accepts an `academy.training.action` recordset,
            a single ID, or a list/tuple of IDs. If omitted, actions are
            derived from `source_set`.

        Side effects
        ------------
        - Writes/creates on `academy.training.action.line` (tracking disabled).
        - May unlink `academy.training.action.line` records.
        - Posts a note (subtype `mail.mt_note`) on each affected action.

        Notes
        -----
        - Overwrite-first design: no per-field delta check.
        - No defensive de-duplication on create; uniqueness errors surface so
          upstream data issues can be fixed.

        Returns
        -------
        recordset
            `academy.training.action.line` records that were created or
            overwritten.
        """

        kwargs = kwargs or {}

        _logger.info(
            "Synchronization started: training programs -> training actions."
        )

        # 1) Parse kwargs and set defaults
        optional = kwargs.get("optional", True)
        remove_mismatches = kwargs.get("remove_mismatches", True)
        synchronize_groups = kwargs.get("synchronize_groups", True)
        target_set = self._sta_get_argument_set(
            "target_set", "academy.training.action", **kwargs
        )
        source_set = self._sta_get_argument_set(
            "source_set", "academy.training.program", **kwargs
        )

        # 2) Find training actions for these programs
        action_set = self._sta_get_actions(
            source_set, target_set, synchronize_groups
        )
        grouped_act_set = self._sta_group_by_program(action_set)

        # 3) Fetch program lines; index action lines by program line
        shared_keys = self._sta_get_shared_keys()
        program_set = source_set or action_set.mapped("training_program_id")
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
            values["needs_synchronization"] = False

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
            "Synchronization finished: training programs -> training actions."
        )

        return result_set

    @api.model
    def _sta_get_argument_set(self, key, model_name, **kwargs):
        value = kwargs.get(key, False)
        action_obj = self.env[model_name]

        if not value:
            recordset = action_obj.browse()
        elif isinstance(value, models.Model):
            if value._name == model_name:
                recordset = value
            else:
                recordset = action_obj.browse()
        elif isinstance(value, int):
            recordset = action_obj.browse(value)
        elif isinstance(value, (list, tuple)):
            ids = [v for v in value if isinstance(v, int)]
            recordset = action_obj.browse(ids) if ids else action_obj.browse()
        else:
            recordset = action_obj.browse()

        return recordset

    @api.model
    def _sta_get_actions(self, source_set, target_set, synchronize_groups):
        """
        Return the training actions to synchronize.

        Selection rules:
          - source_set & target_set -> intersection.
          - only source_set         -> actions of those programs.
          - only target_set         -> exactly those actions.
          - neither                 -> empty recordset.
        """
        action_obj = self.env["academy.training.action"]

        if not source_set and not target_set:
            actions = action_obj.browse()
        else:
            domain = []

            if source_set:
                self_leaf = ("training_program_id", "in", source_set.ids)
                domain.append(self_leaf)

            if target_set:
                target_leaf = ("id", "in", target_set.ids)
                domain.append(target_leaf)

            if not synchronize_groups:
                parent_leaf = ("parent_id", "=", False)
                domain.append(parent_leaf)

            actions = action_obj.search(domain)

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

        return prog_line_obj.shared_keys

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
        """Overwrites the given lines with `values` (write-dict),
        disabling tracking. Does not compare differences.
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
