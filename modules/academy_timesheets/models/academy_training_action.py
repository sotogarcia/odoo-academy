# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools.safe_eval import safe_eval
from odoo.osv.expression import FALSE_DOMAIN, TRUE_DOMAIN
from odoo.addons.academy_base.utils.helpers import OPERATOR_MAP, one2many_count

from pytz import timezone
from datetime import datetime, time, timedelta
from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingAction(models.Model):
    """Button to open session calendar"""

    _name = "academy.training.action"
    _inherit = ["academy.training.action"]

    session_ids = fields.One2many(
        string="Sessions",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="All sessions for training action",
        comodel_name="academy.training.session",
        inverse_name="training_action_id",
        domain=[],
        context={},
        auto_join=False,
    )

    # -- session_count: field and logic ---------------------------------------

    session_count = fields.Integer(
        string="Session count",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help="Number of sessions on which the calculation has been made",
        compute="_compute_session_count",
        search="search_session_count",
    )

    @api.depends("session_ids")
    def _compute_session_count(self):
        counts = one2many_count(self, "session_ids")

        for record in self:
            record.session_count = counts.get(record.id, 0)

    @api.model
    def search_session_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = one2many_count(self.search([]), "session_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    # -------------------------------------------------------------------------

    draft_session_ids = fields.One2many(
        string="Draft sessions",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="All sessions in draft state for training action",
        comodel_name="academy.training.session",
        inverse_name="training_action_id",
        domain=[("state", "=", "draft")],
        context={},
        auto_join=False,
    )

    # -- draft_session_count: field and logic ---------------------------------

    draft_session_count = fields.Integer(
        string="Draft count",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help="Number of sessions in draft state",
        compute="_compute_draft_session_count",
        search="search_draft_session_count",
    )

    @api.depends("draft_session_ids")
    def _compute_draft_session_count(self):
        counts = one2many_count(self, "draft_session_ids")

        for record in self:
            record.draft_session_count = counts.get(record.id, 0)

    @api.model
    def search_draft_session_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = one2many_count(self.search([]), "draft_session_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    # -------------------------------------------------------------------------

    allow_overlap = fields.Boolean(
        string="Allow overlap",
        required=False,
        readonly=False,
        index=False,
        default=False,
        help=(
            "Check to allow sessions for this training action to be "
            "overlapped"
        ),
    )

    # -- current_week_hours: field and logic ----------------------------------

    current_week_hours = fields.Float(
        string="Current week hours",
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 12),
        help="Number of training hours in the current week",
        compute="_compute_current_week_hours",
    )

    @api.depends("session_ids.date_start", "session_ids.date_stop")
    def _compute_current_week_hours(self):
        # Obtener zona horaria del usuario
        user_tz = self.env.user.tz or "UTC"
        local_tz = timezone(user_tz)

        # Establecer el rango de inicio y finalización de la semana actual
        today = datetime.now(local_tz).date()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=7)

        start_of_week = datetime.combine(start_of_week, time.min)
        end_of_week = datetime.combine(end_of_week, time.min)

        start_of_week = local_tz.localize(start_of_week)
        end_of_week = local_tz.localize(end_of_week)

        # Convertir las fechas a UTC
        start_of_week_utc = start_of_week.astimezone(timezone("UTC"))
        end_of_week_utc = end_of_week.astimezone(timezone("UTC"))

        start_of_week_utc = start_of_week_utc.replace(tzinfo=None)
        end_of_week_utc = end_of_week_utc.replace(tzinfo=None)

        for record in self:
            total_hours = 0

            for session in record.session_ids:
                if not (session.date_start and session.date_stop):
                    continue

                if not (start_of_week_utc < session.date_stop):
                    continue

                if not (end_of_week_utc > session.date_start):
                    continue

                session_start = max(start_of_week_utc, session.date_start)
                session_stop = min(end_of_week_utc, session.date_stop)

                duration = max(timedelta(), session_stop - session_start)
                total_hours += duration.total_seconds() / 3600

            record.current_week_hours = total_hours

    # -- Public methods
    # -------------------------------------------------------------------------

    def view_timesheets(self):
        action_xid = (
            "academy_timesheets."
            "action_academy_training_action_timesheet_act_window"
        )
        action = self.env.ref(action_xid)

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.context))

        if self:
            domain = [("training_action_id", "in", self.mapped("id"))]
        else:
            domain = TRUE_DOMAIN

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": action.res_model,
            "target": action.target,
            "name": action.name,
            "view_mode": action.view_mode,
            "domain": domain,
            "context": ctx,
            "search_view_id": action.search_view_id.id,
            "help": action.help,
        }

        return serialized

    def view_sessions(self):
        self.ensure_one()

        action_xid = "academy_timesheets.action_sessions_act_window"
        action = self.env.ref(action_xid)

        # Replace calendar view
        calendar_view_xid = (
            "academy_timesheets.view_academy_training_"
            "session_calendar_no_training"
        )
        views = self._updated_views(action, calendar_view_xid)

        name = self.env._("Sessions for {}").format(self.name)

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.context))
        ctx.update({"default_training_action_id": self.id})

        domain = [("training_action_id", "=", self.id)]

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": "academy.training.session",
            "target": "current",
            "name": name,
            "view_mode": action.view_mode,
            "domain": domain,
            "context": ctx,
            "search_view_id": action.search_view_id.id,
            "help": action.help,
            "views": views,
        }

        return serialized

    def copy_weekly_sessions(self, invite_all=True):
        now = fields.Datetime.now()
        now = now.replace(hour=0, minute=0, second=0, microsecond=0)

        week_start = now - timedelta(days=now.weekday())
        next_week_start = week_start + timedelta(days=7)

        action_ids = self.mapped("id")

        session_domain = [
            "&",
            ("training_action_id", "in", action_ids),
            "|",
            "&",
            ("date_start", ">=", week_start),
            ("date_start", "<", next_week_start),
            "&",
            ("date_stop", ">=", week_start),
            ("date_stop", "<", next_week_start),
        ]
        session_obj = self.env["academy.training.session"]
        session_set = session_obj.search(session_domain)

        target_set = session_set.copy_all()
        if invite_all:
            target_set.invite_all()

        return target_set

    def get_reference(self):
        """Required by clone wizard

        Returns:
            str: model,id
        """

        self.ensure_one()

        return "{},{}".format(self._name, self.id)

    # -- Auxiliary methods
    # -------------------------------------------------------------------------

    def _updated_views(self, action, xid):
        views = [list(view) for view in action.views]
        view = self.env.ref(xid)

        for index in range(0, len(views)):
            if views[index][1] == view.type:
                views[index][0] = view.id

        return views
