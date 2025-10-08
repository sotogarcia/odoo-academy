# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools.safe_eval import safe_eval

from logging import getLogger
from datetime import timedelta, time, datetime

_logger = getLogger(__name__)


class AcademyTimesheetsVerificationWizard(models.TransientModel):
    """Allow to check if all the training actions has a valid timesheet for
    given time interval.

    """

    _name = "academy.timesheets.verification.wizard"
    _description = "Academy timesheets verification wizard"

    _rec_name = "id"
    _order = "id DESC"

    date_start = fields.Date(
        string="Date start",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.compute_next_monday(0),
        help=False,
    )

    date_stop = fields.Date(
        string="Date stop",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.compute_next_monday(6),
        help=False,
    )

    training_action_ids = fields.Many2many(
        string="Training actions",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_training_action_ids(),
        help="Chosen training actions",
        comodel_name="academy.training.action",
        relation="academy_timesheets_verification_wizard_training_action_rel",
        column1="wizard_id",
        column2="training_action_id",
        domain=[],
        context={},
    )

    @api.onchange("date_start", "date_stop", "training_action_ids")
    def _onchange_training_action_ids(self):
        session_set = self._search_sessions()

        action_ids = self._real_id(self.training_action_ids)
        compare_ids = session_set.mapped("training_action_id.id")
        no_set = [item for item in action_ids if item not in compare_ids]
        self.no_sessions_count = len(no_set)

        without_facility = session_set.filtered(
            lambda x: not x.reservation_ids
        )
        self.no_facility_count = len(without_facility)

        without_teacher = session_set.filtered(
            lambda x: not x.teacher_assignment_ids
        )
        self.no_teacher_count = len(without_teacher)

        in_draft_state = session_set.filtered(lambda x: x.state == "draft")
        self.draft_state_count = len(in_draft_state)

    no_sessions_count = fields.Integer(
        string="No sessions",
        required=True,
        readonly=False,
        index=False,
        default=0,
        help="Number of training actions with no sessions",
    )

    no_facility_count = fields.Integer(
        string="No facility",
        required=True,
        readonly=False,
        index=False,
        default=0,
        help="Number of training sessions with no facilities",
    )

    no_teacher_count = fields.Integer(
        string="No teacher",
        required=True,
        readonly=False,
        index=False,
        default=0,
        help="Number of training sessions with no teacher",
    )

    draft_state_count = fields.Integer(
        string="Draft",
        required=True,
        readonly=False,
        index=False,
        default=0,
        help="Number of training sessions in draft state",
    )

    @api.depends_context("lang")
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.name
            record.display_name = self.env._("Schedule verification")

    def default_training_action_ids(self):
        action_set = self.env["academy.training.action"]
        domain = []

        active_model = self.env.context.get("active_model")
        if active_model == "academy.training.action":
            active_ids = self.env.context.get("active_ids", [])
            if not active_ids:
                active_id = self.env.context.get("active_id", False)
                if active_id:
                    active_ids = [active_id]

            if active_ids:
                domain = [("id", "in", active_ids)]

        action_set = action_set.search(domain)

        return action_set

    def compute_next_monday(self, offset=0):
        today = fields.Date.context_today(self)
        monday = today + timedelta(days=(7 - today.weekday()))

        return monday + timedelta(days=offset)

    @staticmethod
    def _real_id(record_set, single=False):
        """Return a list with no NewId's of a single no NewId"""

        result = []

        if record_set and single:
            record_set.ensure_one()

        for record in record_set:
            if isinstance(record.id, models.NewId):
                result.append(record._origin.id)
            else:
                result.append(record.id)

        if single:
            result = result[0] if len(result) == 1 else None

        return result

    def _search_sessions(self):
        action_ids = self._real_id(self.training_action_ids)

        lbound = datetime.combine(self.date_start, time.min)
        ubound = datetime.combine(self.date_stop + timedelta(days=1), time.min)

        lbound = lbound.strftime("%Y-%m-%d %H:%M-%S")
        ubound = ubound.strftime("%Y-%m-%d %H:%M-%S")

        session_domain = [
            "&",
            "&",
            ("training_action_id", "in", action_ids),
            ("date_start", ">=", lbound),
            ("date_start", "<", ubound),
        ]
        session_obj = self.env["academy.training.session"]
        session_set = session_obj.search(session_domain)

        return session_set

    def view_no_sessions_count(self):
        self.ensure_one()

        action_xid = "academy_base.action_training_action_act_window"
        act_wnd = self.env.ref(action_xid)

        name = self.env._("Actions without sessions")

        session_set = self._search_sessions()
        action_ids = self._real_id(self.training_action_ids)
        compare_ids = session_set.mapped("training_action_id.id")
        no_set = [item for item in action_ids if item not in compare_ids]

        domain = [("id", "in", no_set)]
        view_mode = self._reorder_view_mode(act_wnd.view_mode, "kanban")

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": act_wnd.res_model,
            "target": "current",
            "name": name,
            "view_mode": view_mode,
            "domain": domain,
            "context": safe_eval(act_wnd.context),
            "search_view_id": act_wnd.search_view_id.id,
            "help": act_wnd.help,
        }

        return serialized

    def view_no_facility_count(self):
        self.ensure_one()

        action_xid = "academy_timesheets.action_sessions_act_window"
        act_wnd = self.env.ref(action_xid)

        name = self.env._("Actions without sessions")

        session_set = self._search_sessions()
        without_facility = session_set.filtered(
            lambda x: not x.reservation_ids
        )
        without_facility_ids = without_facility.mapped("id")

        domain = [("id", "in", without_facility_ids)]
        view_mode = self._reorder_view_mode(act_wnd.view_mode, "kanban")

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": act_wnd.res_model,
            "target": "current",
            "name": name,
            "view_mode": view_mode,
            "domain": domain,
            "context": safe_eval(act_wnd.context),
            "search_view_id": act_wnd.search_view_id.id,
            "help": act_wnd.help,
        }

        return serialized

    def view_no_teacher_count(self):
        self.ensure_one()

        action_xid = "academy_timesheets.action_sessions_act_window"
        act_wnd = self.env.ref(action_xid)

        name = self.env._("Actions without sessions")

        session_set = self._search_sessions()
        without_teacher = session_set.filtered(
            lambda x: not x.teacher_assignment_ids
        )
        without_teacher_ids = without_teacher.mapped("id")

        domain = [("id", "in", without_teacher_ids)]
        view_mode = self._reorder_view_mode(act_wnd.view_mode, "kanban")

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": act_wnd.res_model,
            "target": "current",
            "name": name,
            "view_mode": view_mode,
            "domain": domain,
            "context": safe_eval(act_wnd.context),
            "search_view_id": act_wnd.search_view_id.id,
            "help": act_wnd.help,
        }

        return serialized

    def view_draft_state_count(self):
        self.ensure_one()

        action_xid = "academy_timesheets.action_sessions_act_window"
        act_wnd = self.env.ref(action_xid)

        name = self.env._("Actions without sessions")

        session_set = self._search_sessions()
        in_draft_state = session_set.filtered(lambda x: x.state == "draft")
        draft_state_ids = in_draft_state.mapped("id")

        domain = [("id", "in", draft_state_ids)]
        view_mode = self._reorder_view_mode(act_wnd.view_mode)

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": act_wnd.res_model,
            "target": "current",
            "name": name,
            "view_mode": view_mode,
            "domain": domain,
            "context": safe_eval(act_wnd.context),
            "search_view_id": act_wnd.search_view_id.id,
            "help": act_wnd.help,
        }

        return serialized

    @staticmethod
    def _reorder_view_mode(view_mode, view="tree"):
        view_mode = view_mode.split(",")
        tree_index = view_mode.index(view)
        tree_item = view_mode.pop(tree_index)
        view_mode.insert(0, tree_item)

        return ",".join(view_mode)
