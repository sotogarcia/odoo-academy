# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval
from ..utils.record_utils import ensure_recordset, get_active_records

from logging import getLogger
from operator import eq, ne

_logger = getLogger(__name__)


class AcademyTrainingActionSynchronizeWizard(models.TransientModel):
    """Synchronize parent training actions with children training actions."""

    _name = "academy.training.action.synchronize.wizard"
    _description = "Academy training action synchronize"

    _rec_name = "id"
    _order = "id DESC"

    parent_action_ids = fields.Many2many(
        string="Parent actions",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Parent training actions will be used as the source for "
        "synchronization.",
        comodel_name="academy.training.action",
        relation="academy_training_action_synchronize_wizard_parent_rel",
        column1="wizard_id",
        column2="training_action_id",
        domain=[("parent_id", "=", False), ("child_ids", "!=", False)],
        context={},
    )

    parent_action_count = fields.Integer(
        string="No. of parents",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help="Total number of parent training actions",
        compute="_compute_parent_action_count",
    )

    @api.depends("parent_action_ids")
    def _compute_parent_action_count(self):
        for record in self:
            record.parent_action_count = len(record.parent_action_ids)

    optional = fields.Boolean(
        string="Include optional",
        required=False,
        readonly=False,
        index=False,
        default=True,
        help="Append optional program lines from parent training action to "
        "its children during synchronization.",
    )

    remove_mismatches = fields.Boolean(
        string="Remove mismatches",
        required=False,
        readonly=False,
        index=False,
        default=True,
        help="Remove child action lines that do not match the source parent "
        "action.",
    )

    child_action_ids = fields.Many2many(
        string="Training groups",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Child training actions will be synchronized with their parent "
        "action",
        comodel_name="academy.training.action",
        relation="academy_training_action_synchronize_wizard_child_rel",
        column1="wizard_id",
        column2="child_action_id",
        domain=[("parent_id", "!=", False), ("child_ids", "=", False)],
        context={},
    )

    child_action_count = fields.Integer(
        string="No. of actions",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help="Number of given target training actions",
        compute="_compute_child_action_count",
    )

    @api.depends("child_action_ids")
    def _compute_child_action_count(self):
        for record in self:
            record.child_action_count = len(record.child_action_ids)

    @api.model
    def call_wizard(self, **kwargs):
        """Open the wizard and prefill fields from kwargs.

        Keyword Args:
            optional (bool): Preselect appending optional program lines.
                Defaults to False.
            remove_mismatches (bool): Preselect removing target lines that
                are not present in the program of the source training action.
            parent_action_ids (recordset|int|list[int]): Source parent training
                actions (academy.training.action) as a recordset, id or list
                of ids.
            child_action_ids (recordset|int|list[int]): Target child training
                actions (academy.training.action) as a recordset, id or list
                of ids.
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
        }

        field, model = "parent_action_ids", "academy.training.action"
        parent_actions = self._get_records(kwargs, field, model)
        if parent_actions:
            m2m_op = [(6, 0, parent_actions.ids)]
            values[field] = m2m_op

        field, model = "child_action_ids", "academy.training.action"
        child_actions = self._get_records(kwargs, field, model)
        if child_actions:
            m2m_op = [(6, 0, child_actions.ids)]
            values[field] = m2m_op

        new_wizard = self.create(values)

        if kwargs.get("show_dialog", True):
            return self.view_wizard(new_wizard)

        return new_wizard

    def view_wizard(self, wizard=None):
        wizard = (wizard and wizard[0]) or self

        action_xid = "{}.{}".format(
            "academy_base",
            "action_academy_training_action_synchronize_wizard_act_window",
        )
        act_wnd = wizard.env.ref(action_xid)

        context = wizard.env.context.copy()
        ctx_from_action = safe_eval(
            act_wnd.context or "{}",
            {"uid": wizard.env.uid, "context": context},
        )
        context.update(ctx_from_action)

        domain = safe_eval(
            act_wnd.domain or "[]", {"uid": wizard.env.uid, "context": context}
        )

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

        return self.synchronize_training_groups(
            optional=self.optional,
            remove_mismatches=self.remove_mismatches,
            source_set=self.parent_action_ids,
            target_set=self.child_action_ids,
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

    # -- Method: synchronize_training_groups and auxiliary logic
    # -------------------------------------------------------------------------

    @api.model
    def synchronize_training_groups(self, **kwargs):
        """
        Synchronize a parent action’s snapshot lines into its child actions
        (“groups”).

        This routine overwrites existing child action lines to mirror the
        parent’s lines, creates missing ones, optionally removes orphans,
        and posts a short note in the chatter of each affected child action.
        It also aligns each child action’s training program with its parent
        when they differ.

        Workflow
        --------
        1) Determine parent and child actions from kwargs (parents in
           `source_set`, children in `target_set`; infer the missing side
           from the other).
        2) Align each child’s `training_program_id` to the parent and group
           children by parent.
        3) Compute shared fields to sync (chatter/technical fields excluded).
        4) For each parent snapshot line:
           - Build a write-format dict from that line.
           - Overwrite all matched child lines (tracking disabled).
           - If allowed, stage create-values for missing child lines.
        5) Bulk-create missing child lines (tracking disabled).
        6) Optionally unlink child lines with no matching parent snapshot.
        7) Post one sync note per affected child action.

        Parameters (kwargs)
        -------------------
        optional : bool, default True
            If False, skip creation of optional lines; existing ones are still
            overwritten.
        remove_mismatches : bool, default True
            If True, delete child lines that do not match any parent snapshot
            line. Match rules:
              * If the child has `program_line_id`, match by
                (parent_action_id, program_line_id).
              * Otherwise match by (parent_action_id, code) when the parent
                line has no `program_line_id` and shares the same `code`.
        source_set : recordset | int | Iterable[int], optional
            Set of **parent** actions to sync from. Accepts an
            `academy.training.action` recordset, a single ID, or a list/tuple
            of IDs. If omitted, it is inferred from `target_set` via each
            child’s `parent_id`.
        target_set : recordset | int | Iterable[int], optional
            Set of **child** actions to sync to. Accepts an
            `academy.training.action` recordset, a single ID, or a list/tuple
            of IDs. If omitted, children are derived from `source_set`.
        changes_only: bool, default False
            If True, the update step is limited to lines marked as needing
            synchronization, except when the parent action line itself is
            marked as needing synchronization; in that case all related
            action lines are updated.
        sync_details : bool, default True
            If True, child actions are first aligned with their parent
            action (core fields and ``training_program_id``). If False,
            only action lines are synchronized, leaving child action
            headers unchanged.

        Side effects
        ------------
        - Writes/creates on `academy.training.action.line` (tracking disabled).
        - May unlink `academy.training.action.line` records.
        - May update a child action’s `training_program_id` to match its
          parent.
        - Posts a note (subtype `mail.mt_note`) on each affected child action.

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
            "Synchronization started: parent action -> child actions."
        )

        # 1) Parse kwargs and set defaults
        optional = kwargs.get("optional", True)
        remove_mismatches = kwargs.get("remove_mismatches", True)
        source_set = self._sta_get_argument_set("source_set", "==", **kwargs)
        target_set = self._sta_get_argument_set("target_set", "!=", **kwargs)
        changes_only = kwargs.get("changes_only", False)
        sync_details = kwargs.get("sync_details", True)

        # 2) Find child actions, align program with parent and group by parent
        children_set = self._stg_get_children(source_set, target_set)
        grp_child_set = self._stg_grouped_by_parent(children_set)
        if sync_details:
            self._stg_synchronize_details(children_set)

        # 3) Fetch program lines; index child lines by parent snapshot line
        shared_keys = self._stg_get_shared_keys()
        parent_set = source_set or children_set.mapped("parent_id")
        parent_line_set = parent_set.mapped("action_line_ids")
        child_line_set = children_set.mapped("action_line_ids")
        by_parent_line = self._stg_group_child_lines(child_line_set)

        # 4) For each program line, sync related action lines
        act_line_obj = self.env["academy.training.action.line"]
        empty_act_line = act_line_obj.browse()
        result_set = act_line_obj.browse()
        creation_value_list = []
        for parent_line in parent_line_set:
            values = self._stg_read_source_values(parent_line, shared_keys)
            values["needs_synchronization"] = False

            # 5) Update existing lines (optionally only changed ones)
            full_line_set = by_parent_line.get(parent_line.id, empty_act_line)
            if changes_only and not parent_line.needs_synchronization:
                update_set = full_line_set.filtered("needs_synchronization")
            else:
                update_set = full_line_set

            if update_set:
                result_set |= self._stg_update_lines(update_set, values)

            # 6) Skip creation for optional lines (optional=False)
            if parent_line.optional and not optional:
                continue

            # 7.a) Compute missing actions and build create values
            create_over_set = self._stg_compute_create_over(
                parent_line, grp_child_set, full_line_set
            )
            values_list = self._stg_create_values(create_over_set, values)
            if values_list:
                creation_value_list.extend(values_list)

        # 7.b) Create missing lines (bulk)
        result_set |= self._stg_create_lines(creation_value_list)

        # 8) Remove action lines without a matching program line
        self._stg_unlink(parent_line_set, child_line_set, remove_mismatches)

        # 9) Chatter note on all lines touched (created or overwritten)
        self._notify_synchronization(result_set)

        _logger.info(
            "Synchronization finished: parent action -> child actions."
        )

        return result_set

    @api.model
    def _sta_get_argument_set(self, key, parent_op, **kwargs):
        value = kwargs.get(key, False)
        action_obj = self.env["academy.training.action"]

        valid_operators = {"==": eq, "!=": ne}
        assert parent_op in valid_operators, "Invalid comparison operator"
        operator = valid_operators.get(parent_op)

        if not value:
            recordset = action_obj.browse()
        elif isinstance(value, models.Model):
            if value._name == "academy.training.action":
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

        return recordset.filtered(
            lambda rec: operator(bool(rec.parent_id), False)
        )

    def _stg_get_children(self, source_set, target_set):
        """
        Return the training actions to synchronize.

        Selection rules:
          - source_set & target_set -> source_set.child_ids ∩ target_set.
          - only source_set         -> source_set.child_ids.
          - only target_set         -> target_set (only child actions).
          - neither                 -> empty recordset.
        """
        action_obj = self.env["academy.training.action"]

        if not source_set and not target_set:
            child_actions = action_obj.browse()
        else:
            domain = []

            if source_set:
                self_leaf = ("parent_id", "in", source_set.ids)
                domain.append(self_leaf)

            if target_set:
                target_leaf = [
                    ("id", "in", target_set.ids),
                    ("parent_id", "!=", False),
                ]
                domain.extend(target_leaf)

            child_actions = action_obj.search(domain)

        _logger.debug(
            "Synchronization scope: %d training action(s) selected.",
            len(child_actions),
        )

        return child_actions

    @staticmethod
    def _stg_grouped_by_parent(children_set):
        """Group child actions by parent training action.

        Return:
            dict: child training actions grouped by parent action id.
        """
        grouped_by_parent = {}

        for child in children_set:
            parent = child.parent_id
            if not parent:
                continue

            # Group record by parent action
            parent_id = parent.id
            if parent_id not in grouped_by_parent:
                grouped_by_parent[parent_id] = child
            else:
                grouped_by_parent[parent_id] |= child

        return grouped_by_parent

    @api.model
    def _stg_read_action_values(self, action):
        """Build values dict from shared program keys."""

        if not action:
            return {}

        action.ensure_one()

        program_obj = self.env["academy.training.program"]
        shared_keys = program_obj.shared_keys

        raw_values = {key: action[key] for key in shared_keys}
        converted_values = action._convert_to_write(raw_values)

        return converted_values

    @api.model
    def _stg_synchronize_details(self, child_set):
        """Synchronize child actions with their parent actions."""

        grouped_by_parent = {}

        for child in child_set:
            parent = child.parent_id
            if not parent:
                continue

            # Group record by parent action
            if parent not in grouped_by_parent:
                grouped_by_parent[parent] = child
            else:
                grouped_by_parent[parent] |= child

        # Set training program from parent
        if grouped_by_parent:
            ctx = dict(tracking_disable=True, mail_create_nosubscribe=True)

            for parent, children_of_parent in grouped_by_parent.items():
                values = self._stg_read_action_values(parent)
                child_actions = children_of_parent.with_context(ctx)
                program = parent.training_program_id
                if program:
                    values["training_program_id"] = program.id
                child_actions.write(values)

    @staticmethod
    def _stg_group_child_lines(child_line_set):
        grouped_by_parent_line = {}

        action_line_obj = child_line_set.env["academy.training.action.line"]
        empty_record = action_line_obj.browse()
        parent_lines = child_line_set.mapped(
            "training_action_id.parent_id.action_line_ids"
        )

        for child_line in child_line_set:
            parent_id = child_line.training_action_id.parent_id.id
            prog_line_id = child_line.program_line_id.id
            code = child_line.code

            parent_line = empty_record
            if prog_line_id:
                parent_line = parent_lines.filtered(
                    lambda pl: pl.training_action_id.id == parent_id
                    and pl.program_line_id.id == prog_line_id
                )
            elif code:
                parent_line = parent_lines.filtered(
                    lambda pl: pl.training_action_id.id == parent_id
                    and (not pl.program_line_id and pl.code == code)
                )

            if not parent_line:
                continue

            parent_line = parent_line[:1]
            parent_line_id = parent_line.id
            if parent_line_id not in grouped_by_parent_line:
                grouped_by_parent_line[parent_line_id] = child_line
            else:
                grouped_by_parent_line[parent_line_id] |= child_line

        return grouped_by_parent_line

    @staticmethod
    def _stg_unlink(parent_lines, child_lines, remove_mismatches):
        """Remove child lines with no matching parent snapshot line.

        Match rules:
          - If child has program_line_id, match by
            (parent_action_id, program_line_id).
          - Else match by (parent_action_id, code) where parent line
            has no program_line_id and shares the same code.
        """
        if not remove_mismatches:
            return

        # Build allowed keys from parent snapshot lines (per parent_id)
        allowed_map = {}
        for pl in parent_lines:
            parent_id = pl.training_action_id.id
            row = allowed_map.get(parent_id)
            if not row:
                row = {"prog_ids": set(), "codes": set()}
                allowed_map[parent_id] = row

            if pl.program_line_id:
                row["prog_ids"].add(pl.program_line_id.id)
            elif pl.code:
                row["codes"].add(pl.code)

        def _has_match(line):
            parent = line.training_action_id.parent_id
            parent_id = parent.id if parent else None
            if not parent_id:
                return False

            allowed_row = allowed_map.get(parent_id)
            if not allowed_row:
                return False

            if line.program_line_id:
                return line.program_line_id.id in allowed_row["prog_ids"]
            if line.code:
                return line.code in allowed_row["codes"]

            return False

        to_unlink = child_lines.filtered(lambda line: not _has_match(line))

        _logger.debug(
            "Synchronization cleanup: will remove %d unmatched child "
            "action line(s).",
            len(to_unlink),
        )

        if to_unlink:
            to_unlink.unlink()

    def _stg_get_shared_keys(self):
        prog_line_obj = self.env["academy.training.program.line"]

        return prog_line_obj.shared_keys

    @staticmethod
    def _stg_read_source_values(parent_line, shared_keys):
        raw = {k: parent_line[k] for k in shared_keys}
        values = parent_line._convert_to_write(raw)

        return values

    @api.model
    def _stg_compute_create_over(self, parent_line, children_set, update_set):
        parent_id = parent_line.training_action_id.id
        related_action_set = children_set.get(
            parent_id, self.env["academy.training.action"].browse()
        )

        updated_action_set = update_set.mapped("training_action_id")

        return related_action_set - updated_action_set

    def _stg_update_lines(self, child_line_set, values):
        """Overwrite child lines with the given write-dict values."""
        if not child_line_set:
            return child_line_set

        _logger.debug(
            "Synchronization updates: %d action line(s) will be overwritten.",
            len(child_line_set),
        )
        vals2write = dict(values)
        # Never move lines between actions on updates
        vals2write.pop("training_action_id", None)
        # Reduce chatter and tracking noise
        ctx = dict(tracking_disable=True, mail_create_nosubscribe=True)
        child_line_set.with_context(ctx).write(vals2write)

        return child_line_set

    @staticmethod
    def _stg_create_values(create_over_set, base_values):
        values = dict(base_values)
        creation_value_list = []

        for action in create_over_set:
            creation_values = values.copy()
            creation_values["training_action_id"] = action.id
            creation_value_list.append(creation_values)

        return creation_value_list

    def _stg_create_lines(self, creation_value_list):
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

        # Silence tracking, followers and email notifications
        ctx = {
            "tracking_disable": True,
            "mail_notrack": True,
            "mail_create_nosubscribe": True,
            "mail_post_autofollow": False,
            "mail_notify_force_send": False,
        }
        body = self.env._(
            "Synchronization: this training action was synchronized from "
            "its parent action."
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
