# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from contextlib import contextmanager
from logging import getLogger

_logger = getLogger(__name__)

_CRON_TASK_XID = "academy_base.ir_cron_academy_maintenance_task"
_LOCK_KEY = "academy_maintenance_task"
_MSG_BEGIN = "Academy maintenance: hour=%s, tasks=%d"
_MSG_TASK = "Executing task: %s.%s, freq=%s, offset=%s"
_MSG_OK = "Task OK: %s.%s"
_MSG_MISSING = "Task missing: %s"
_MSG_FAILED = "Task FAILED: %s.%s (rolled back)"

_FREQUENCY_MAP = {
    "freq_1": 1,
    "freq_2": 2,
    "freq_3": 3,
    "freq_4": 4,
    "freq_6": 6,
    "freq_8": 8,
    "freq_12": 12,
    "freq_24": 24,
}


class AcademyMaintenanceTask(models.Model):
    _name = "academy.maintenance.task"
    _description = "Academy maintenance task"
    _rec_name = "display_name"
    _order = "sequence, id"

    active = fields.Boolean(
        string="Active",
        required=False,
        readonly=False,
        index=True,
        default=True,
        help="Enable or disable the execution of this task.",
    )

    sequence = fields.Integer(
        string="Sequence",
        required=True,
        readonly=False,
        index=True,
        default=10,
        help="Lower values run first when multiple tasks match the same hour.",
    )

    model_id = fields.Many2one(
        string="Model",
        required=True,
        readonly=True,
        index=True,
        default=None,
        help="Target model on which the method will be executed.",
        comodel_name="ir.model",
        ondelete="cascade",
        auto_join=False,
    )

    method = fields.Char(
        string="Method",
        required=True,
        readonly=True,
        index=True,
        default=None,
        help="Model-level method name to call (decorated with @api.model).",
        translate=False,
    )

    frequency = fields.Selection(
        string="Frequency",
        required=True,
        readonly=False,
        index=True,
        default="freq_1",
        help="How often this task should run within the 24-hour cycle.",
        selection=[
            ("freq_1", "Hourly (every 1 hour)"),
            ("freq_2", "Every 2 hours (bi-hourly)"),
            ("freq_3", "Every 3 hours"),
            ("freq_4", "Every 4 hours (quarter-daily)"),
            ("freq_6", "Every 6 hours"),
            ("freq_8", "Every 8 hours (three times a day)"),
            ("freq_12", "Every 12 hours (twice a day)"),
            ("freq_24", "Daily (once a day)"),
        ],
    )

    offset = fields.Integer(
        string="Offset",
        required=True,
        readonly=False,
        index=True,
        default=0,
        help=(
            "Hour offset within the frequency cycle. For example, with "
            "'Every 8 hours', offsets 0/1/2... schedule at 00/01/02... then "
            "+8 and +16. Valid range is 0..(divisor-1)."
        ),
    )

    _sql_constraints = [
        (
            "uniq_model_method",
            "unique(model_id, method)",
            "A method should be listed only once per model.",
        ),
    ]

    @api.depends(
        "model_id", "method", "frequency", "offset", "active", "sequence"
    )
    def _compute_display_name(self):
        for rec in self:
            model = rec.model_id.model if rec.model_id else "?"
            rec.display_name = f"{model}.{rec.method or '?'}"

    def _get_frequency_value(self):
        self.ensure_one()
        return _FREQUENCY_MAP.get(self.frequency or "freq_1", 1)

    @api.constrains("method")
    def _check_mt_name_syntax(self):
        message = _(
            "Method must be a valid Python identifier "
            "(letters, digits, underscores) starting with a letter."
        )
        for rec in self:
            if (
                not rec.method
                or not rec.method.replace("_", "").isalnum()
                or not rec.method[0].isalpha()
            ):
                raise ValidationError(message)

    @api.constrains("model_id", "method")
    def _check_method_exists(self):
        for rec in self:
            if not rec.model_id or not rec.method:
                continue
            try:
                model = self.env[rec.model_id.model]
            except KeyError:
                raise ValidationError(
                    _("Model not found: %s") % rec.model_id.model
                )
            if not hasattr(model, rec.method):
                raise ValidationError(
                    _("Method '%(m)s' not found on model '%(model)s'")
                    % {"m": rec.method, "model": rec.model_id.model}
                )

    @api.constrains("frequency", "offset")
    def _check_offset_range(self):
        for rec in self:
            divisor = rec._get_frequency_value()
            if rec.offset < 0 or rec.offset >= divisor:
                raise ValidationError(
                    _(
                        "Offset must be between 0 and %(max)d for this frequency."
                    )
                    % {"max": divisor - 1}
                )

    # ---- Scheduler entrypoint (called once per hour by ir.cron) -----------------

    @api.model
    @contextmanager
    def advisory_lock(self, key: str, block: bool = False):
        """
        Advisory lock bound to current DB connection (cursor).
        Yields True if lock is held, False otherwise (when non-blocking).
        Always unlocks on exit if it was locked.
        """
        if block:
            self.env.cr.execute(
                "SELECT pg_advisory_lock(hashtext(%s))", (key,)
            )
            locked = True
        else:
            self.env.cr.execute(
                "SELECT pg_try_advisory_lock(hashtext(%s))", (key,)
            )
            locked = bool(self.env.cr.fetchone()[0])
        try:
            yield locked
        finally:
            if locked:
                self.env.cr.execute(
                    "SELECT pg_advisory_unlock(hashtext(%s))", (key,)
                )

    @api.model
    def _get_cron_user(self):
        """Return the cron's user (fallback to current env user)."""
        cron = self.env.ref(_CRON_TASK_XID, raise_if_not_found=False)
        return cron.user_id or self.env.user

    @api.model
    def _now_local_for_user(self, user=None):
        """Return 'now' localized for the given user (fallback UTC)."""
        user = user or self.env.user
        now_utc = fields.Datetime.now()
        return fields.Datetime.context_timestamp(self.with_user(user), now_utc)

    @api.model
    def _search_tasks_for_hour(self, hour_slot):
        """
        Return a recordset of tasks matching the given hour slot.
        Applies domain, active flag, order and optional limit.
        """
        domain = [("active", "=", True)]
        tasks = self.search(domain, order="sequence ASC, id ASC")

        matched_ids = []
        for task in tasks:
            div = task._get_frequency_value()
            if (hour_slot % div) == (task.offset % div):
                matched_ids.append(task.id)

        return self.browse(matched_ids)

    @api.model
    def _run_isolated(self, cr, user_id, md_name, mt_name, context=None):
        """Create a temp env and run a @api.model method on a model name."""
        env = api.Environment(cr, user_id, context or self.env.context)
        target_model = env[md_name].sudo()
        if not hasattr(target_model, mt_name):
            raise NotImplementedError(
                "Method not found: %s.%s" % (md_name, mt_name)
            )
        getattr(target_model, mt_name)()

    @api.model
    def perform_maintenance(self):
        """
        Run all active tasks whose (current hour % divisor) == offset.
        Each task runs in its own cursor; commit/rollback isolated.
        """

        with self.advisory_lock(_LOCK_KEY, block=False) as locked:
            if not locked:
                _logger.info(
                    "Maintenance skipped: another run holds the lock."
                )
                return False

            cron_user = self._get_cron_user()
            now_local = self._now_local_for_user(user=cron_user)

            hour_slot = now_local.hour  # 0..23
            task_set = self._search_tasks_for_hour(hour_slot)

            context = self.env.context

            _logger.info(_MSG_BEGIN, hour_slot, len(task_set))

            for task in task_set:
                md_name = task.model_id.model
                mt_name = task.method

                frequency = task.frequency
                offset = task.offset
                _logger.debug(_MSG_TASK, md_name, mt_name, frequency, offset)

                with self.env.registry.cursor() as new_cr:
                    try:
                        self._run_isolated(
                            new_cr, cron_user.id, md_name, mt_name, context
                        )
                        _logger.info(_MSG_OK, md_name, mt_name)
                        new_cr.commit()

                    except NotImplementedError as nie:
                        _logger.error(_MSG_MISSING, nie, exc_info=True)
                        new_cr.rollback()

                    except Exception:
                        _logger.exception(_MSG_FAILED, md_name, mt_name)
                        new_cr.rollback()

                    finally:
                        new_cr.close()
