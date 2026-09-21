###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
#                                                                             #
#    IMPORTANT: modules adding new academy maintenance tasks must extend      #
#    AcademyMaintenanceTask._get_allowed_tasks() to explicitly authorize      #
#    each (model, method) pair. See that method's docstring for the required  #
#    extension pattern and an implementation example.                         #
###############################################################################

from contextlib import contextmanager
from logging import getLogger

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

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

    # -- Model configuration
    # -------------------------------------------------------------------------

    IMMUTABLE_FIELDS = [  # noqa: RUF012
        "model_id",
        "method",
    ]

    # -- Entity fields
    # -------------------------------------------------------------------------

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

    # -- SQL constraints
    # -------------------------------------------------------------------------

    _sql_constraints = [  # noqa: RUF012
        (
            "uniq_model_method",
            "unique(model_id, method)",
            "A method should be listed only once per model.",
        ),
    ]

    # -- Computed fields
    # -------------------------------------------------------------------------

    @api.depends(
        "model_id",
        "method",
        "frequency",
        "offset",
        "active",
        "sequence",
    )
    def _compute_display_name(self):
        for rec in self:
            model = rec.model_id.model if rec.model_id else "?"
            rec.display_name = f"{model}.{rec.method or '?'}"

    # -- Constraints
    # -------------------------------------------------------------------------

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
                    % {
                        "m": rec.method,
                        "model": rec.model_id.model,
                    }
                )

    @api.constrains("model_id", "method")
    def _check_allowed_task(self):
        for record in self:
            if record.model_id and record.method:
                record._ensure_allowed_task(
                    record.model_id.model,
                    record.method,
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
                    % {
                        "max": divisor - 1,
                    }
                )

    # -- Overridden methods
    # -------------------------------------------------------------------------

    def write(self, values):
        self._prevent_change_immutable_fields(values)

        return super().write(values)

    # -- Maintenance task registry and security
    # -------------------------------------------------------------------------

    @api.model
    def _get_allowed_tasks(self):
        """Return the maintenance tasks explicitly allowed for execution.

        Maintenance tasks are identified by a ``(model_name, method_name)`` pair,
        where ``model_name`` is the technical name of an Odoo model and
        ``method_name`` is the name of a model-level method that can be executed
        by ``academy.maintenance.task``.

        Only tasks returned by this method are considered valid. This allowlist is
        checked both when maintenance task records are validated and immediately
        before a task is executed.

        Dependent modules that need to register additional maintenance tasks must
        extend this method rather than replacing the existing allowlist. The
        inherited implementation should call ``super()`` and add its own
        ``(model_name, method_name)`` pairs to the returned set.

        Example::

            @api.model
            def _get_allowed_tasks(self):
                allowed_tasks = super()._get_allowed_tasks()

                allowed_tasks.add(
                    (
                        "my.model",
                        "my_maintenance_task",
                    )
                )

                return allowed_tasks

        The registered method is expected to be callable on the model recordset
        without positional arguments, normally as a model-level maintenance
        method.

        Adding a task to this allowlist does not bypass Odoo access rights or
        record rules. Maintenance methods are executed using the effective user
        of the operation: the configured cron user for scheduled execution and
        the current user for manual execution.

        Returns:
            set[tuple[str, str]]: Allowed ``(model_name, method_name)`` pairs.
        """
        return {
            (
                "academy.training.action",
                "training_action_synchronize_task",
            ),
            (
                "academy.training.action.enrolment",
                "full_enrolment_maintenance_task",
            ),
        }

    @api.model
    def _ensure_allowed_task(self, model_name, method_name):
        """Ensure that a maintenance task is explicitly authorized.

        Args:
            model_name (str): Technical name of the target Odoo model.
            method_name (str): Model-level maintenance method to execute.

        Returns:
            bool: True when the task is explicitly allowed.

        Raises:
            ValidationError: If the ``(model_name, method_name)`` pair is not
                registered by ``_get_allowed_tasks()``.
        """
        allowed_tasks = self._get_allowed_tasks()

        if (model_name, method_name) not in allowed_tasks:
            raise ValidationError(
                self.env._(
                    "Maintenance task '%(model)s.%(method)s' is not allowed."
                )
                % {
                    "model": model_name,
                    "method": method_name,
                }
            )

        return True

    # -- Public methods
    # -------------------------------------------------------------------------

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

                _logger.debug(
                    _MSG_TASK,
                    md_name,
                    mt_name,
                    frequency,
                    offset,
                )

                try:
                    with self.env.registry.cursor() as new_cr:
                        self._run_isolated(
                            new_cr,
                            cron_user.id,
                            md_name,
                            mt_name,
                            context,
                        )

                    _logger.info(_MSG_OK, md_name, mt_name)

                except NotImplementedError:
                    _logger.exception(_MSG_MISSING)

                except Exception:
                    _logger.exception(
                        _MSG_FAILED,
                        md_name,
                        mt_name,
                    )

    def execute_right_now(self):
        """Execute the configured maintenance task immediately."""
        self.ensure_one()

        model_name = self.model_id.model
        method_name = self.method

        self._ensure_allowed_task(
            model_name,
            method_name,
        )

        target_model = self.env[model_name]
        method_to_execute = getattr(target_model, method_name)

        method_to_execute()

    # -- Scheduler helpers
    # -------------------------------------------------------------------------

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
                "SELECT pg_advisory_lock(hashtext(%s))",
                (key,),
            )
            locked = True
        else:
            self.env.cr.execute(
                "SELECT pg_try_advisory_lock(hashtext(%s))",
                (key,),
            )
            locked = bool(self.env.cr.fetchone()[0])

        try:
            yield locked
        finally:
            if locked:
                self.env.cr.execute(
                    "SELECT pg_advisory_unlock(hashtext(%s))",
                    (key,),
                )

    @api.model
    def _get_cron_user(self):
        """Return the maintenance cron user or the current user as fallback.

        The user configured on the maintenance cron is used when both the cron
        record and its user are available. If the cron XMLID cannot be resolved,
        or the cron has no user configured, the current environment user is
        returned instead.

        Returns:
            res.users: User under which maintenance tasks should be executed.
        """
        cron = self.env.ref(
            _CRON_TASK_XID,
            raise_if_not_found=False,
        )

        if cron and cron.user_id:
            return cron.user_id

        return self.env.user

    @api.model
    def _now_local_for_user(self, user=None):
        """Return the current datetime localized for the given user.

        The timezone configured on the supplied user is used explicitly, avoiding
        any ``tz`` value inherited from the current environment context. If no user
        is supplied, the current environment user is used. If that user has no
        timezone configured, UTC is used as fallback.

        Args:
            user (res.users, optional): User whose timezone should be used.
                Defaults to the current environment user.

        Returns:
            datetime: Timezone-aware current datetime localized to the user's
            timezone, or UTC when no timezone is configured.
        """
        user = user or self.env.user
        timezone = user.tz or "UTC"

        recordset = self.with_user(user).with_context(tz=timezone)
        now_utc = fields.Datetime.now()

        return fields.Datetime.context_timestamp(
            recordset,
            now_utc,
        )

    @api.model
    def _search_tasks_for_hour(self, hour_slot):
        """Return tasks matching the given hour slot.

        Applies the active flag and sequence-based ordering.
        """
        domain = [
            ("active", "=", True),
        ]
        tasks = self.search(
            domain,
            order="sequence ASC, id ASC",
        )

        matched_ids = []

        for task in tasks:
            divisor = task._get_frequency_value()

            if (hour_slot % divisor) == (task.offset % divisor):
                matched_ids.append(task.id)

        return self.browse(matched_ids)

    @api.model
    def _run_isolated(self, cr, user_id, md_name, mt_name, context=None):
        """Execute an allowed model method using an isolated database cursor.

        A dedicated Odoo environment is created for the supplied cursor and user.
        The target method is executed with the access rights and record rules of
        that user; no privilege escalation is performed by this method.

        Before execution, the ``(model_name, method_name)`` pair is checked against
        the maintenance task allowlist.

        Transaction management is intentionally left to the caller. In particular,
        when the supplied cursor is used as a context manager, Odoo commits on
        successful completion and rolls back automatically when an exception
        escapes the context.

        Args:
            cr (odoo.sql_db.Cursor): Database cursor used for the isolated
                transaction.
            user_id (int): User ID used to build the isolated environment.
            md_name (str): Technical name of the target model.
            mt_name (str): Name of the model method to execute.
            context (dict | None, optional): Context for the isolated environment.
                Defaults to the current environment context.

        Raises:
            ValidationError: If the requested task is not explicitly allowed.
            NotImplementedError: If the requested method does not exist on the
                target model.
        """
        context = self.env.context if context is None else context

        env = api.Environment(
            cr,
            user_id,
            context,
        )

        maintenance_obj = env["academy.maintenance.task"]
        maintenance_obj._ensure_allowed_task(
            md_name,
            mt_name,
        )

        target_model = env[md_name]

        if not hasattr(target_model, mt_name):
            raise NotImplementedError(f"Method not found: {md_name}.{mt_name}")

        getattr(target_model, mt_name)()

    # -- Auxiliary methods
    # -------------------------------------------------------------------------

    def _get_frequency_value(self):
        self.ensure_one()

        return _FREQUENCY_MAP.get(
            self.frequency or "freq_1",
            1,
        )

    def _prevent_change_immutable_fields(self, values):
        """Prevent immutable fields from being changed after record creation."""
        field_names = set(self.IMMUTABLE_FIELDS) & set(values)
        if not field_names:
            return True

        message = _(
            "The field '%(field)s' cannot be modified once the record "
            "has been created."
        )

        for record in self:
            for field_name in field_names:
                current_value = record[field_name]

                if isinstance(current_value, models.BaseModel):
                    current_value = current_value.id

                new_value = values[field_name]

                if isinstance(new_value, models.BaseModel):
                    new_value = new_value.id

                current_value = current_value or False
                new_value = new_value or False

                if current_value != new_value:
                    raise ValidationError(
                        message
                        % {
                            "field": record._fields[field_name].string,
                        }
                    )

        return True
