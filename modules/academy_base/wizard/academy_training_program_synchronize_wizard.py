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

        source_programs = (
            self.source_program_ids or self.env["academy.training.program"]
        )

        return source_programs.synchronize_training_actions(
            optional=self.optional,
            remove_mismatches=self.remove_mismatches,
            synchronize_groups=self.synchronize_groups,
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
