# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError, UserError
from odoo.osv.expression import AND
from odoo.tools import safe_eval

from datetime import timedelta, datetime
from logging import getLogger


_logger = getLogger(__name__)


class AcademyTimesheetsCloneWizard(models.TransientModel):
    """Clone all sessions from a given date or week"""

    _name = "academy.timesheets.clone.wizard"
    _description = "Academy timesheets clone wizard"

    _rec_name = "id"
    _order = "id DESC"

    interval_type = fields.Selection(
        string="Interval",
        required=True,
        readonly=False,
        index=False,
        default="week",
        help=False,
        selection=[("day", "Day"), ("week", "Week")],
    )

    method = fields.Selection(
        string="Method",
        required=True,
        readonly=False,
        index=False,
        default="replace",
        help=False,
        selection=[("replace", "Replace"), ("append", "Append")],
    )

    from_start = fields.Date(
        string="Start (source)",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.compute_current_monday(offset=0),
        help="Start date of the interval from which sessions will be copied",
    )

    @api.onchange("from_start", "interval_type")
    def _onchange_from_start(self):
        if self.interval_type == "week":
            weekday = self.from_start.weekday()
            if weekday != 0:
                self.from_start = self.from_start - timedelta(days=weekday)

    from_stop = fields.Date(
        string="End (source)",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="End date of the interval from which sessions will be copied",
        compute="_compute_from_stop",
    )

    @api.depends("interval_type", "from_start")
    def _compute_from_stop(self):
        for record in self:
            if record.interval_type == "day":
                record.from_stop = record.from_start
            else:
                record.from_stop = record.from_start + timedelta(days=6)

    to_start = fields.Date(
        string="Start (target)",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.compute_current_monday(offset=7),
        help="Start date of the interval from which sessions will be copied",
    )

    @api.onchange("to_start", "interval_type")
    def _onchange_to_start(self):
        if self.interval_type == "week":
            weekday = self.to_start.weekday()
            if weekday != 0:
                self.to_start = self.to_start - timedelta(days=weekday)

    to_stop = fields.Date(
        string="End (target)",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="End date of the interval from which sessions will be copied",
        compute="_compute_to_stop",
    )

    @api.depends("interval_type", "to_start")
    def _compute_to_stop(self):
        for record in self:
            if record.interval_type == "day":
                record.to_stop = record.to_start
            else:
                record.to_stop = record.to_start + timedelta(days=6)

    model_id = fields.Many2one(
        string="Model",
        required=False,
        readonly=True,
        index=False,
        default=lambda self: self.default_model_id(),
        help="Source recordset model",
        comodel_name="ir.model",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    def default_model_id(self):
        model_set = self.env["ir.model"]

        active_model = self.env.context.get("active_model", False)
        if active_model:
            model_domain = [("model", "=", active_model)]
            model_set = model_set.search(model_domain, limit=1)

        return model_set

    record_count = fields.Integer(
        string="Targets",
        required=True,
        readonly=True,
        index=False,
        default=lambda self: self.default_record_count(),
        help="Number of source records",
    )

    def default_record_count(self):
        active_ids = self._get_context_active_ids()
        return len(active_ids)

    state = fields.Selection(
        string="State",
        required=True,
        readonly=False,
        index=True,
        default="draft",
        help="Cloned session status",
        selection=[("draft", "Draft"), ("ready", "Ready")],
    )

    autoinvite = fields.Boolean(
        string="Invite all",
        required=False,
        readonly=False,
        index=False,
        default=True,
        help="Check it to invite all students",
    )

    show_logs = fields.Boolean(
        string="Show logs",
        required=False,
        readonly=False,
        index=False,
        default=True,
        help="Check it to show log history on exit",
    )

    tracking_disable = fields.Boolean(
        string="Tracking disable",
        required=False,
        readonly=False,
        index=False,
        default=True,
        help="Disable tracking",
    )

    def compute_current_monday(self, offset=0):
        today = fields.Date.context_today(self)
        monday = today - timedelta(days=today.weekday())

        return monday + timedelta(days=offset)

    def _get_consistent_dates(self):
        """Gets valid dates for the selected interval type even if they are
        not set correctly in the wizard.

        It increase the end dates by one day to use them as the limit of the
        ranges. [start - stop)

        Returns:
            tuple: from_start, from_stop, to_start, to_stop
        """
        from_start = self.from_start
        to_start = self.to_start

        if self.interval_type == "week":
            from_start = from_start - timedelta(days=from_start.weekday())
            to_start = to_start - timedelta(days=to_start.weekday())

            from_stop = from_start + timedelta(days=6)
            to_stop = to_start + timedelta(days=6)
        else:
            from_stop, to_stop = from_start, to_start

        from_stop = from_stop + timedelta(days=1)
        to_stop = to_stop + timedelta(days=1)

        return from_start, from_stop, to_start, to_stop

    @staticmethod
    def are_dates_overlapped(from_start, from_stop, to_start, to_stop):
        """Check if ranges [start-stop) are overlapped

        Args:
            from_start (datetime): lower bound of the first range
            from_stop (datetime): upper bound of the first range
            to_start (datetime): lower bound of the second range
            to_stop (datetime): upper bound of the second range

        Returns:
            bool: True if the are overlapped or False otherwise
        """

        return (to_start >= from_start and to_start < from_stop) or (
            to_stop >= from_start and to_stop < from_stop
        )

    def _get_context_active_ids(self):
        context = self.env.context

        active_ids = context.get("active_ids", [])
        if not active_ids:
            active_id = context.get("active_id", False)
            if active_id:
                active_ids = [active_id]

        return active_ids

    def _search_targets(self):
        model = self.model_id.model
        target_set = self.env[model]

        active_ids = self._get_context_active_ids()
        if active_ids:
            target_domain = [("id", "in", active_ids)]
            target_set = target_set.search(target_domain)
        else:
            msg = self.env._("No records selected for which to clone sessions")
            _logger.info(msg)

        return target_set

    @api.model
    def _compute_target_domain(self, target_set):
        target_ids = target_set.mapped("id")

        def mtype(model):
            return type(self.env[model])

        if isinstance(target_set, mtype("academy.training.action")):
            field = "training_action_id.id"
        elif isinstance(target_set, mtype("academy.teacher")):
            field = "teacher_assignment_ids.teacher_id.id"
        else:
            UserError(_("Invalid target model"))

        return [(field, "in", target_ids)]

    @staticmethod
    def _compute_interval_domain(start, stop):
        start = start.strftime("%Y-%m-%d %H:%M:%S")
        stop = stop.strftime("%Y-%m-%d %H:%M:%S")
        return ["&", ("date_start", ">=", start), ("date_stop", "<", stop)]

    def _search_sessions(self, target_set, start, stop):
        session_set = self.env["academy.training.session"]

        if target_set:
            target_domain = self._compute_target_domain(target_set)
            inverval_domain = self._compute_interval_domain(start, stop)

            session_domain = AND([target_domain, inverval_domain])

            session_set = session_set.search(session_domain)

        return session_set

    @staticmethod
    def _compute_new_interval(session, target_date):
        date_start = datetime.combine(target_date, session.date_start.time())
        date_stop = datetime.combine(target_date, session.date_stop.time())

        date_start = date_start.strftime("%Y-%m-%d %H:%M:%S")
        date_stop = date_stop.strftime("%Y-%m-%d %H:%M:%S")

        return {"date_start": date_start, "date_stop": date_stop}

    def perform_action(self):
        self.ensure_one()

        if self.tracking_disable:
            tracking_disable_ctx = self.env.context.copy()
            tracking_disable_ctx.update({"tracking_disable": True})
            self = self.with_context(tracking_disable_ctx)

        log_obj = self.env["academy.timesheets.clone.wizard.log"]
        sequence = 10

        from_start, from_stop, to_start, to_stop = self._get_consistent_dates()

        if self.are_dates_overlapped(from_start, from_stop, to_start, to_stop):
            msg = self.env._("Source and destination ranges must not overlap")
            raise ValidationError(msg)

        target_set = self._search_targets()
        if not target_set:
            msg = self.env._("No records selected for which to clone sessions")
            raise ValidationError(msg)

        for target in target_set:
            sequence = log_obj.target(sequence, self, target)

            for offset in range(0, (from_stop - from_start).days):
                from_date = from_start + timedelta(days=offset)
                to_date = to_start + timedelta(days=offset)
                sequence = log_obj.dates(
                    sequence, self, target, from_date, to_date
                )

                if self.method == "replace":
                    session_set = self._search_sessions(
                        target, to_date, to_date + timedelta(days=1)
                    )

                    for session in session_set:
                        sequence = log_obj.found(
                            sequence, self, target, from_date, session
                        )

                        try:
                            self.env.cr.commit()
                            session.unlink()
                            self.env.cr.commit()
                        except Exception as ex:
                            self.env.cr.rollback()
                            sequence = log_obj.no_delete(
                                sequence, self, target, from_date, session, ex
                            )
                        else:
                            sequence = log_obj.delete(
                                sequence, self, target, from_date
                            )

                session_set = self._search_sessions(
                    target, from_date, from_date + timedelta(days=1)
                )
                for session in session_set:
                    try:
                        defaults = self._compute_new_interval(session, to_date)

                        self.env.cr.commit()
                        session.copy(defaults)
                        if self.autoinvite:
                            session.invite_all()
                        self.env.cr.commit()

                    except Exception as ex:
                        self.env.cr.rollback()
                        sequence = log_obj.no_clone(
                            sequence,
                            self,
                            target,
                            from_date,
                            to_date,
                            session,
                            ex,
                        )
                    else:
                        sequence = log_obj.clone(
                            sequence, self, target, from_date, to_date, session
                        )

        return self._view_logs()

    def _view_logs(self):
        self.ensure_one()

        action_xid = "academy_timesheets.action_clone_wizard_log_act_window"
        action = self.env.ref(action_xid)

        name = self.env._("Log history #{}").format(self.id)

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.context))
        ctx.update({"search_default_error_logs": 1})

        domain = [("wizard_code", "=", self.id)]

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": "academy.timesheets.clone.wizard.log",
            "target": "current",
            "name": name,
            "view_mode": action.view_mode,
            "domain": domain,
            "context": ctx,
            "search_view_id": action.search_view_id.id,
            "help": action.help,
        }

        return serialized
