# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from logging import getLogger

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.osv.expression import AND
from odoo.tools import safe_eval
from odoo.tools.translate import _

_logger = getLogger(__name__)


class _CloneLogState:
    """Track the current log sequence."""

    def __init__(self, log_model, initial_sequence=10):
        self.log_model = log_model
        self.sequence = initial_sequence


@dataclass(frozen=True)
class _CloneDateRanges:
    """Store normalized source and destination date ranges."""

    source_start: date
    source_stop: date
    destination_start: date
    destination_stop: date


class AcademyTimesheetsCloneWizard(models.TransientModel):
    """Clone sessions from a selected day, week, or month."""

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
        selection=[
            ("day", "Day"),
            ("week", "Week"),
            ("month", "Month"),
        ],
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
        default=lambda self: self._get_current_monday(day_offset=0),
        help="Start date of the interval from which sessions will be copied",
    )

    from_stop = fields.Date(
        string="End (source)",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="End date of the interval from which sessions will be copied",
        compute="_compute_from_stop",
    )

    to_start = fields.Date(
        string="Start (target)",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self._get_current_monday(day_offset=7),
        help="Start date of the interval to which sessions will be copied",
    )

    to_stop = fields.Date(
        string="End (target)",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="End date of the interval to which sessions will be copied",
        compute="_compute_to_stop",
    )

    model_id = fields.Many2one(
        string="Model",
        required=False,
        readonly=True,
        index=False,
        default=lambda self: self._find_active_model(),
        help="Model of the selected clone targets",
        comodel_name="ir.model",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    record_count = fields.Integer(
        string="Targets",
        required=True,
        readonly=True,
        index=False,
        default=lambda self: self._get_active_record_count(),
        help="Number of selected clone targets",
    )

    state = fields.Selection(
        string="State",
        required=True,
        readonly=False,
        index=True,
        default="draft",
        help="Cloned session status",
        selection=[("keep", "Keep"), ("draft", "Draft"), ("ready", "Ready")],
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

    # -------------------------------------------------------------------------
    # Field callbacks
    # -------------------------------------------------------------------------

    @api.onchange("from_start", "interval_type")
    def _onchange_from_start(self):
        """Normalize the source start date for the selected interval."""
        if not self.from_start:
            return

        if self.interval_type == "week":
            source_weekday = self.from_start.weekday()
            if source_weekday != 0:
                self.from_start -= timedelta(days=source_weekday)
        elif self.interval_type == "month":
            self.from_start = self.from_start.replace(day=1)

    @api.depends("interval_type", "from_start")
    def _compute_from_stop(self):
        """Compute the source interval end date."""
        for wizard in self:
            if not wizard.from_start:
                wizard.from_stop = False
            elif wizard.interval_type == "day":
                wizard.from_stop = wizard.from_start
            elif wizard.interval_type == "week":
                wizard.from_stop = wizard.from_start + timedelta(days=6)
            elif wizard.interval_type == "month":
                wizard.from_stop = wizard._get_month_end(wizard.from_start)

    @api.onchange("to_start", "interval_type")
    def _onchange_to_start(self):
        """Normalize the destination start date for the selected interval."""
        if not self.to_start:
            return

        if self.interval_type == "week":
            destination_weekday = self.to_start.weekday()
            if destination_weekday != 0:
                self.to_start -= timedelta(days=destination_weekday)
        elif self.interval_type == "month":
            self.to_start = self.to_start.replace(day=1)

    @api.depends("interval_type", "to_start")
    def _compute_to_stop(self):
        """Compute the destination interval end date."""
        for wizard in self:
            if not wizard.to_start:
                wizard.to_stop = False
            elif wizard.interval_type == "day":
                wizard.to_stop = wizard.to_start
            elif wizard.interval_type == "week":
                wizard.to_stop = wizard.to_start + timedelta(days=6)
            elif wizard.interval_type == "month":
                wizard.to_stop = wizard._get_month_end(wizard.to_start)

    # -------------------------------------------------------------------------
    # Context and defaults
    # -------------------------------------------------------------------------

    def _find_active_model(self):
        """Find the model associated with the active records."""
        active_model_name = self.env.context.get("active_model", False)
        if not active_model_name:
            return self.env["ir.model"]

        active_model_domain = [("model", "=", active_model_name)]
        return self.env["ir.model"].search(active_model_domain, limit=1)

    def _get_active_record_count(self):
        """Return the number of active records."""
        active_record_ids = self._get_active_record_ids()
        return len(active_record_ids)

    def _get_current_monday(self, day_offset=0):
        """Return the current Monday plus the requested day offset."""
        current_date = fields.Date.context_today(self)
        current_monday = current_date - timedelta(days=current_date.weekday())

        return current_monday + timedelta(days=day_offset)

    def _get_active_record_ids(self):
        """Return active record IDs from the current context."""
        active_record_ids = self.env.context.get("active_ids", [])
        if not active_record_ids:
            active_record_id = self.env.context.get("active_id", False)
            if active_record_id:
                active_record_ids = [active_record_id]

        return active_record_ids

    def _get_clone_execution_context(self):
        """Return the wizard with tracking disabled when requested."""
        if not self.tracking_disable:
            return self

        tracking_disabled_context = self.env.context.copy()
        tracking_disabled_context.update({"tracking_disable": True})

        return self.with_context(tracking_disabled_context)

    # -------------------------------------------------------------------------
    # Date ranges
    # -------------------------------------------------------------------------

    def _get_consistent_date_ranges(self):
        """Return normalized source and destination ranges as [start, stop)."""
        source_start = self.from_start
        destination_start = self.to_start

        if self.interval_type == "week":
            source_start -= timedelta(days=source_start.weekday())
            destination_start -= timedelta(days=destination_start.weekday())

            source_stop = source_start + timedelta(days=6)
            destination_stop = destination_start + timedelta(days=6)

        elif self.interval_type == "month":
            source_start = source_start.replace(day=1)
            destination_start = destination_start.replace(day=1)

            source_stop = self._get_month_end(source_start)
            destination_stop = self._get_month_end(destination_start)

        else:
            source_stop = source_start
            destination_stop = destination_start

        source_stop += timedelta(days=1)
        destination_stop += timedelta(days=1)

        return _CloneDateRanges(
            source_start=source_start,
            source_stop=source_stop,
            destination_start=destination_start,
            destination_stop=destination_stop,
        )

    def _validate_non_overlapping_date_ranges(self, date_ranges):
        """Validate that source and destination ranges do not overlap."""
        if self._has_date_range_overlap(date_ranges):
            message = _("Source and destination ranges must not overlap")
            raise ValidationError(message)

    @staticmethod
    def _has_date_range_overlap(date_ranges):
        """Return whether source and destination ranges overlap."""
        return (
            date_ranges.source_start < date_ranges.destination_stop
            and date_ranges.destination_start < date_ranges.source_stop
        )

    @staticmethod
    def _get_source_day_count(date_ranges):
        """Return the number of days in the source range."""
        return (date_ranges.source_stop - date_ranges.source_start).days

    @staticmethod
    def _get_destination_day_count(date_ranges):
        """Return the number of days in the destination range."""
        return (
            date_ranges.destination_stop - date_ranges.destination_start
        ).days

    def _get_copy_day_count(self, date_ranges):
        """Return the number of source days that can be copied."""
        return min(
            self._get_source_day_count(date_ranges),
            self._get_destination_day_count(date_ranges),
        )

    def _get_day_offsets_to_process(self, date_ranges):
        """Return the day offsets that must be processed."""
        if self._should_replace_destination_sessions():
            day_count = self._get_destination_day_count(date_ranges)
        else:
            day_count = self._get_copy_day_count(date_ranges)

        return range(day_count)

    @staticmethod
    def _get_source_date_for_offset(
        date_ranges,
        copy_day_count,
        day_offset,
    ):
        """Return the source date corresponding to a day offset."""
        if day_offset >= copy_day_count:
            return None

        return date_ranges.source_start + timedelta(days=day_offset)

    @staticmethod
    def _get_month_end(date_value):
        """Return the last day of the month containing the given date."""
        month_start = date_value.replace(day=1)
        next_month_start = month_start + relativedelta(months=1)
        month_end = next_month_start - relativedelta(days=1)

        if isinstance(month_end, datetime):
            return month_end.date()

        return month_end

    # -------------------------------------------------------------------------
    # Business rules
    # -------------------------------------------------------------------------

    def _should_replace_destination_sessions(self):
        """Return whether destination sessions must be replaced."""
        return self.method == "replace"

    def _should_invite_cloned_session(self):
        """Return whether students must be invited to cloned sessions."""
        return bool(self.autoinvite)

    # -------------------------------------------------------------------------
    # Clone targets and sessions
    # -------------------------------------------------------------------------

    def _find_clone_targets(self):
        """Find the records selected as clone targets."""
        clone_target_model_name = self.model_id.model
        clone_target_model = self.env[clone_target_model_name]

        active_record_ids = self._get_active_record_ids()
        if not active_record_ids:
            message = _("No records selected for which to clone sessions")
            _logger.info(message)
            return clone_target_model

        clone_target_domain = [("id", "in", active_record_ids)]
        return clone_target_model.search(clone_target_domain)

    @staticmethod
    def _validate_clone_targets(clone_targets):
        """Validate that at least one clone target exists."""
        if not clone_targets:
            message = _("No records selected for which to clone sessions")
            raise ValidationError(message)

    @api.model
    def _get_clone_target_domain(self, clone_target):
        """Return the session domain for the given clone target."""
        clone_target_ids = clone_target.ids
        clone_target_model_name = clone_target._name

        if clone_target_model_name == "academy.training.action":
            target_field_name = "training_action_id.id"
        elif clone_target_model_name == "academy.teacher":
            target_field_name = "teacher_assignment_ids.teacher_id.id"
        else:
            raise UserError(_("Invalid target model"))

        return [(target_field_name, "in", clone_target_ids)]

    @staticmethod
    def _get_session_interval_domain(interval_start, interval_stop):
        """Return the session domain for the given date interval."""
        serialized_interval_start = interval_start.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        serialized_interval_stop = interval_stop.strftime("%Y-%m-%d %H:%M:%S")

        return [
            "&",
            ("date_start", ">=", serialized_interval_start),
            ("date_start", "<", serialized_interval_stop),
        ]

    def _find_target_sessions_for_date(self, clone_target, session_date):
        """Find sessions for a clone target on the given date."""
        training_session_model = self.env["academy.training.session"]
        interval_stop = session_date + timedelta(days=1)

        clone_target_domain = self._get_clone_target_domain(clone_target)
        interval_domain = self._get_session_interval_domain(
            session_date,
            interval_stop,
        )
        session_domain = AND([clone_target_domain, interval_domain])

        return training_session_model.search(session_domain)

    def _get_cloned_session_state(self, source_session):
        """Return the state to assign to a cloned session."""
        if self.state == "keep":
            return source_session.state

        return self.state

    def _get_session_clone_values(
        self,
        source_session,
        destination_date,
    ):
        """Return the values used to create a cloned session."""
        session_duration = source_session.date_stop - source_session.date_start

        destination_start = datetime.combine(
            destination_date,
            source_session.date_start.time(),
        )
        destination_stop = destination_start + session_duration

        return {
            "date_start": destination_start.strftime("%Y-%m-%d %H:%M:%S"),
            "date_stop": destination_stop.strftime("%Y-%m-%d %H:%M:%S"),
            "state": self._get_cloned_session_state(source_session),
        }

    # -------------------------------------------------------------------------
    # Clone processing
    # -------------------------------------------------------------------------

    def perform_action(self):
        """Clone the selected sessions according to the wizard settings."""
        self.ensure_one()

        execution_wizard = self._get_clone_execution_context()

        date_ranges = execution_wizard._get_consistent_date_ranges()
        execution_wizard._validate_non_overlapping_date_ranges(date_ranges)

        clone_targets = execution_wizard._find_clone_targets()
        execution_wizard._validate_clone_targets(clone_targets)

        log_state = _CloneLogState(
            execution_wizard.env["academy.timesheets.clone.wizard.log"]
        )

        execution_wizard._process_clone_targets(
            clone_targets,
            date_ranges,
            log_state,
        )

        if self.show_logs:
            return execution_wizard._get_log_view_action()

    def _process_clone_targets(
        self,
        clone_targets,
        date_ranges,
        log_state,
    ):
        """Process all selected clone targets."""
        copy_day_count = self._get_copy_day_count(date_ranges)
        day_offsets = self._get_day_offsets_to_process(date_ranges)

        for clone_target in clone_targets:
            self._process_clone_target(
                clone_target,
                date_ranges,
                copy_day_count,
                day_offsets,
                log_state,
            )

    def _process_clone_target(
        self,
        clone_target,
        date_ranges,
        copy_day_count,
        day_offsets,
        log_state,
    ):
        """Process all dates for a single clone target."""
        self._log_clone_target(log_state, clone_target)

        for day_offset in day_offsets:
            self._process_clone_date(
                clone_target,
                date_ranges,
                copy_day_count,
                day_offset,
                log_state,
            )

    def _process_clone_date(
        self,
        clone_target,
        date_ranges,
        copy_day_count,
        day_offset,
        log_state,
    ):
        """Process one source-to-destination date mapping."""
        destination_date = date_ranges.destination_start + timedelta(
            days=day_offset
        )

        source_date = self._get_source_date_for_offset(
            date_ranges,
            copy_day_count,
            day_offset,
        )

        if source_date is not None:
            self._log_clone_date_mapping(
                log_state,
                clone_target,
                source_date,
                destination_date,
            )

        if self._should_replace_destination_sessions():
            self._replace_destination_sessions(
                clone_target,
                source_date,
                destination_date,
                log_state,
            )

        elif source_date is not None:
            self._append_source_sessions(
                clone_target,
                source_date,
                destination_date,
                log_state,
            )

    def _delete_destination_session(
        self,
        clone_target,
        log_reference_date,
        destination_session,
        log_state,
    ):
        """Delete one destination session and record the result."""
        self._log_destination_session_found(
            log_state,
            clone_target,
            log_reference_date,
            destination_session,
        )

        destination_session.unlink()

        self._log_destination_session_deleted(
            log_state,
            clone_target,
            log_reference_date,
        )

    def _append_source_sessions(
        self,
        clone_target,
        source_date,
        destination_date,
        log_state,
    ):
        """Append source sessions independently to the destination date."""
        source_sessions = self._find_target_sessions_for_date(
            clone_target,
            source_date,
        )

        for source_session in source_sessions:
            initial_log_sequence = log_state.sequence

            try:
                with self.env.cr.savepoint():
                    self._clone_source_session(
                        clone_target,
                        source_date,
                        destination_date,
                        source_session,
                        log_state,
                    )

            except Exception as exception:  # noqa: BLE001
                log_state.sequence = initial_log_sequence

                self._log_source_session_clone_failure(
                    log_state,
                    clone_target,
                    source_date,
                    destination_date,
                    source_session,
                    exception,
                )

    def _clone_source_session(
        self,
        clone_target,
        source_date,
        destination_date,
        source_session,
        log_state,
    ):
        """Clone one source session and record the result."""
        session_clone_values = self._get_session_clone_values(
            source_session,
            destination_date,
        )

        cloned_session = source_session.copy(session_clone_values)

        if self._should_invite_cloned_session():
            cloned_session.invite_all()

        self._log_source_session_cloned(
            log_state,
            clone_target,
            source_date,
            destination_date,
            source_session,
        )

    def _replace_destination_sessions(
        self,
        clone_target,
        source_date,
        destination_date,
        log_state,
    ):
        """Replace destination sessions atomically for one date."""
        failed_operation = None
        failed_session = None
        initial_log_sequence = log_state.sequence

        try:
            with self.env.cr.savepoint():
                destination_sessions = self._find_target_sessions_for_date(
                    clone_target,
                    destination_date,
                )

                log_reference_date = source_date or destination_date

                for destination_session in destination_sessions:
                    failed_operation = "delete"
                    failed_session = destination_session

                    self._delete_destination_session(
                        clone_target,
                        log_reference_date,
                        destination_session,
                        log_state,
                    )

                if source_date is not None:
                    failed_operation = "clone"
                    failed_session = None

                    source_sessions = self._find_target_sessions_for_date(
                        clone_target,
                        source_date,
                    )

                    for source_session in source_sessions:
                        failed_session = source_session

                        self._clone_source_session(
                            clone_target,
                            source_date,
                            destination_date,
                            source_session,
                            log_state,
                        )

        except Exception as exception:  # noqa: BLE001
            log_state.sequence = initial_log_sequence

            if failed_operation == "delete":
                self._log_destination_session_deletion_failure(
                    log_state,
                    clone_target,
                    log_reference_date,
                    failed_session,
                    exception,
                )

            elif failed_operation == "clone":
                self._log_source_session_clone_failure(
                    log_state,
                    clone_target,
                    source_date,
                    destination_date,
                    failed_session,
                    exception,
                )

    # -------------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------------

    def _log_clone_target(
        self,
        log_state,
        clone_target,
    ):
        """Log the clone target being processed."""
        log_state.sequence = log_state.log_model.target(
            log_state.sequence,
            self,
            clone_target,
        )

    def _log_clone_date_mapping(
        self,
        log_state,
        clone_target,
        source_date,
        destination_date,
    ):
        """Log a source-to-destination date mapping."""
        log_state.sequence = log_state.log_model.dates(
            log_state.sequence,
            self,
            clone_target,
            source_date,
            destination_date,
        )

    def _log_destination_session_found(
        self,
        log_state,
        clone_target,
        log_reference_date,
        destination_session,
    ):
        """Log a destination session found for deletion."""
        log_state.sequence = log_state.log_model.found(
            log_state.sequence,
            self,
            clone_target,
            log_reference_date,
            destination_session,
        )

    def _log_destination_session_deletion_failure(
        self,
        log_state,
        clone_target,
        log_reference_date,
        destination_session,
        exception,
    ):
        """Log a failed destination session deletion."""
        log_state.sequence = log_state.log_model.no_delete(
            log_state.sequence,
            self,
            clone_target,
            log_reference_date,
            destination_session,
            exception,
        )

    def _log_destination_session_deleted(
        self,
        log_state,
        clone_target,
        log_reference_date,
    ):
        """Log a successful destination session deletion."""
        log_state.sequence = log_state.log_model.delete(
            log_state.sequence,
            self,
            clone_target,
            log_reference_date,
        )

    def _log_source_session_clone_failure(
        self,
        log_state,
        clone_target,
        source_date,
        destination_date,
        source_session,
        exception,
    ):
        """Log a failed source session clone."""
        log_state.sequence = log_state.log_model.no_clone(
            log_state.sequence,
            self,
            clone_target,
            source_date,
            destination_date,
            source_session,
            exception,
        )

    def _log_source_session_cloned(
        self,
        log_state,
        clone_target,
        source_date,
        destination_date,
        source_session,
    ):
        """Log a successful source session clone."""
        log_state.sequence = log_state.log_model.clone(
            log_state.sequence,
            self,
            clone_target,
            source_date,
            destination_date,
            source_session,
        )

    def _get_log_view_action(self):
        """Return the action that displays the wizard logs."""
        self.ensure_one()

        log_action_xmlid = (
            "academy_timesheets.action_clone_wizard_log_act_window"
        )
        log_action = self.env.ref(log_action_xmlid)
        action_name = _("Log history #{}").format(self.id)

        action_context = self.env.context.copy()
        action_context.update(safe_eval(log_action.context))
        action_context.update({"search_default_error_logs": 1})

        log_domain = [("wizard_code", "=", self.id)]

        view_action = {
            "type": "ir.actions.act_window",
            "res_model": "academy.timesheets.clone.wizard.log",
            "target": "current",
            "name": action_name,
            "view_mode": log_action.view_mode,
            "domain": log_domain,
            "context": action_context,
            "search_view_id": log_action.search_view_id.id,
            "help": log_action.help,
        }

        return view_action
