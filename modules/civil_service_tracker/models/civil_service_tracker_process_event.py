# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError, UserError

from logging import getLogger
from pytz import timezone, utc
from datetime import datetime, time
from html import escape as html_escape
from validators import url as is_a_valid_url


_logger = getLogger(__name__)


class CivilServiceTrackerProcessEvent(models.Model):
    _name = "civil.service.tracker.process.event"
    _description = "Civil service tracker process event"

    _table = "cst_process_event"

    _rec_name = "name"
    _order = "event_date ASC, name ASC"

    _inherit = ["civil.service.tracker.thread.to.parent.mixin"]

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Name or identifier of the event within a selection process",
        translate=True,
        tracking=True,
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Optional description providing additional context",
        translate=True,
    )

    active = fields.Boolean(
        string="Active",
        required=False,
        readonly=False,
        index=False,
        default=True,
        help="Indicates whether this administrative scope is currently active",
        tracking=True,
    )

    selection_process_id = fields.Many2one(
        string="Selection process",
        required=True,
        readonly=False,
        index=False,
        default=None,
        help="",
        comodel_name="civil.service.tracker.selection.process",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        tracking=True,
    )

    issuer_partner_id = fields.Many2one(
        string="Issuing Entity",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Entity responsible for publishing or announcing this event",
        comodel_name="res.partner",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        tracking=True,
    )

    # - Field: event_type_id (onchange)
    # ------------------------------------------------------------------------

    event_type_id = fields.Many2one(
        string="Event type",
        required=True,
        readonly=False,
        index=False,
        default=None,
        help="",
        comodel_name="civil.service.tracker.event.type",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        tracking=True,
    )

    @api.onchange("event_type_id")
    def _onchange_event_type_id(self):
        if not self.event_type_id:
            return

        new_name = self.event_type_id.name
        current_name = self.name or ""
        previous_name = self._origin.name if self._origin else ""

        # Si es nuevo (sin origen) y el nombre está vacío → asignar el nuevo.
        if not self._origin and not current_name:
            self.name = new_name

        # Si ya existía y no ha sido editado manualmente → asignar el nuevo.
        elif current_name == previous_name and current_name != new_name:
            self.name = new_name

        # Si el tipo de evento es todo el día, es probable que el evento lo sea
        self.all_day = self.event_type_id.all_day

    # ------------------------------------------------------------------------

    unique = fields.Boolean(
        string="Unique",
        readonly=True,
        index=True,
        help="Only one event of this type per process is allowed.",
        related="event_type_id.unique",
        store=True,
    )

    event_date = fields.Datetime(
        string="Event date",
        required=True,
        readonly=False,
        index=True,
        default=fields.datetime.now(),
        help=False,
        tracking=True,
    )

    all_day = fields.Boolean(
        string="All day",
        required=False,
        readonly=False,
        index=True,
        default=True,
        help="Indicates that this event spans the entire day",
        tracking=True,
    )

    attachment_id = fields.Many2one(
        string="Attachment",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="",
        comodel_name="ir.attachment",
        domain=[("res_model", "=", "civil.service.tracker.process.event")],
        context={"default_res_model": "civil.service.tracker.process.event"},
        ondelete="set null",
        auto_join=False,
        tracking=True,
    )

    attach_new_type = fields.Selection(
        string="Attachment type",
        required=True,
        readonly=False,
        index=True,
        default="none",
        help=False,
        selection=[("none", "None"), ("binary", "File"), ("url", "URL")],
        compute="_compute_attach_new_type",
        store=True,
    )

    @api.depends("attachment_id")
    def _compute_attach_new_type(self):
        for record in self:
            record.attach_new_type = record.attachment_id.type or "none"

    attach_new_name = fields.Char(
        string="Upload filename",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        translate=False,
        compute="_compute_attach_new_name",
        store=True,
    )

    @api.depends("attachment_id")
    def _compute_attach_new_name(self):
        for record in self:
            record.attach_new_name = record.attachment_id.name

    attach_new_binary = fields.Binary(
        string="Upload file",
        required=False,
        readonly=False,
        index=False,
        help=False,
        compute="_compute_attach_new_binary",
        store=True,
    )

    @api.depends("attachment_id")
    def _compute_attach_new_binary(self):
        for record in self:
            record.attach_new_binary = record.attachment_id.datas

    attach_new_url = fields.Char(
        string="Attach a URL",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        translate=False,
        compute="_compute_attach_new_url",
        store=True,
    )

    @api.depends("attachment_id")
    def _compute_attach_new_url(self):
        for record in self:
            record.attach_new_url = record.attachment_id.url

    attachment_url = fields.Char(
        string="Attachment URL",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="",
        translate=False,
        related="attachment_id.effective_url",
    )

    # -------------------------------------------------------------------------
    # CONSTRAINTS
    # -------------------------------------------------------------------------

    # _sql_constraints = [
    #     (
    #         "check_name_min_length",
    #         "CHECK(char_length(name) > 3)",
    #         "The name must have more than 3 characters.",
    #     ),
    # ]

    @api.constrains("attach_new_url")
    def _check_attach_new_url(self):
        message_pattern = _("Invalid attachment URL: %s")

        for record in self:
            url = record.attach_new_url
            if url and not is_a_valid_url(url):
                raise ValidationError(message_pattern % url)

    @api.constrains("selection_process_id", "event_type_id", "unique")
    def _check_unique_event_type_per_process(self):
        message = _("Only one event of this type per process is allowed.")
        for record in self:
            if not record.unique:
                continue
            domain = [
                ("selection_process_id", "=", record.selection_process_id.id),
                ("event_type_id", "=", record.event_type_id.id),
                ("unique", "=", True),
                ("id", "!=", record.id),
            ]
            if self.search_count(domain):
                raise ValidationError(message)

    # -------------------------------------------------------------------------
    # OVERWRITTEN METHODS
    # -------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, values_list):
        """Overridden method 'create'"""

        for values in values_list:
            values = self._adjust_event_date_in_values(values)
            self._process_attachment_form(values)

        result = super().create(values_list)

        if "attachment_id" in values:
            result._bind_attachments_to_events()

        result.mapped("selection_process_id").refresh_event_information()

        return result

    def write(self, values):
        """
        Overrides the default `write` method to:
        - Update the message thread if the linked selection process changes.
        - Synchronize related virtual date fields if the event type or event
        date changes.

        Args:
            values (dict): Field values to update.

        Returns:
            bool: Result of the write operation.
        """

        if "event_date" not in values and values.get("all_day"):
            self._adjust_existing_event_dates_for_all_day()

        values = self._adjust_event_date_in_values(values)
        self._check_all_day_consistency_on_event_date_update(values)

        self._process_attachment_form(values)

        parent = super(CivilServiceTrackerProcessEvent, self)
        result = parent.write(values)

        if "attachment_id" in values:
            self._bind_attachments_to_events()

        self.mapped("selection_process_id").refresh_event_information()

        return result

    def unlink(self):
        """Overridden method 'unlink'"""
        processes = self.mapped("selection_process_id")

        parent = super(CivilServiceTrackerProcessEvent, self)
        result = parent.unlink()

        processes.refresh_event_information()

        return result

    def _get_tracking_parent(self):
        """
        Returns the record that will act as the parent thread for chatter
        messages.

        This method is used by the `civil.service.tracker.thread.to.parent.mixin`
        mixin to redirect messages from this model (typically a child record)
        to its logical parent, ensuring that all chatter activity is
        centralized.

        In this case, messages posted on process events will appear in the
        thread of the linked selection process (`selection_process_id`),
        providing a unified communication log.

        Returns:
            models.Model: The record to which the chatter thread should be
            linked.
        """
        return self.selection_process_id

    def _get_tracking_prefix(self):
        return _("Event")

    # -------------------------------------------------------------------------
    # AUXILIARY METHODS
    # -------------------------------------------------------------------------

    def _get_adjusted_event_datetime(self, datetime_value):
        """
        Adjusts a UTC datetime to ensure that 'all-day' events are aligned with
        the  user's local date. If the local date (in the user's timezone)
        differs from the UTC date, returns a datetime set to midnight UTC of
        the local date.

        This prevents all-day events from appearing one day early in the
        calendar view.

        The input may be a datetime or string; the return value will match the
        input type.
        """
        if not datetime_value:
            return datetime_value

        input_is_string = isinstance(datetime_value, str)

        try:
            # Normalize input to datetime object
            if input_is_string:
                dt = fields.Datetime.from_string(datetime_value)
            elif isinstance(datetime_value, datetime):
                dt = datetime_value
            else:
                message = "Unsupported type for datetime_value: %s"
                _logger.warning(message, type(datetime_value))
                return datetime_value

            # Get timezone from context (or default to UTC)
            tz_name = self.env.context.get("tz") or "UTC"
            local_tz = timezone(tz_name)

            # Convert UTC datetime to local timezone
            utc_dt = dt.replace(tzinfo=utc)
            local_dt = utc_dt.astimezone(local_tz).replace(tzinfo=None)

            # If date has changed in local time, reset to midnight of local
            if local_dt.date() != dt.date():
                dt = datetime.combine(local_dt.date(), time.min)

            # Return in original format
            if input_is_string:
                return fields.Datetime.to_string(dt)
            else:
                return dt

        except Exception as e:
            _logger.error("Error adjusting all-day datetime: %s", str(e))
            return datetime_value

    def _adjust_event_date_in_values(self, values):
        """
        If 'event_date' and 'all_day' are both present and all_day is True,
        adjust the event_date to use the configured UTC time.
        """

        if values.get("event_date") and values.get("all_day"):
            adjusted = self._get_adjusted_event_datetime(values["event_date"])
            values["event_date"] = adjusted

        return values

    def _adjust_existing_event_dates_for_all_day(self):
        """
        When records are being updated to all_day=True but event_date is not
        explicitly passed, this adjusts current event_date values.
        """
        records_to_adjust = self.filtered(
            lambda r: not r.all_day and r.event_date
        )

        for record in records_to_adjust:
            adjusted = record._get_adjusted_event_datetime(record.event_date)
            record.write({"event_date": adjusted})

    def _check_all_day_consistency_on_event_date_update(self, values):
        """
        Validates that updating event_date is allowed only when:
        - all_day is being set to True, or
        - all records already have all_day=True
        """
        if "event_date" not in values:
            return

        new_all_day = values.get("all_day")
        label = self._fields["event_date"].string

        if new_all_day is False:
            raise UserError(
                _(
                    "You cannot update the '%s' field when 'All day' is set "
                    "to False."
                )
                % label
            )

        if new_all_day is None and self.filtered(lambda r: not r.all_day):
            raise UserError(
                _(
                    "You cannot update the '%s' field for records where "
                    "'All day' is not enabled."
                )
                % label
            )

    def _process_attachment_form(self, values):
        Attachment = self.env["ir.attachment"]
        attachment = Attachment.browse()  # Empty recordset for default return

        new_type = values.pop("attach_new_type", False)
        new_binary = values.pop("attach_new_binary", False)
        new_url = values.pop("attach_new_url", False)
        new_name = values.pop("attach_new_name", False)

        # Exit early if no type or 'none'
        if not new_type:
            return attachment

        # Prevent massive updates
        if len(self) > 1 and any([new_type, new_binary, new_url, new_name]):
            _logger.warning(
                "To prevent massive update of attachment information, the "
                "attachment form fields have been removed from the update "
                "for selection process event records %s.",
                tuple(self.ids),
            )
            return attachment

        if new_type == "none":
            values["attachment_id"] = None
            if self.attachment_id:
                self.attachment_id.unlink()
            return attachment

        # Determine field to update
        if new_type == "binary":
            if not new_binary or not new_name:
                _logger.debug(
                    f"_process_attachment_form: binary data or name missing"
                )
                return attachment

            data_key, data_value = "datas", new_binary

        elif new_type == "url":
            if not new_url:
                _logger.debug(f"_process_attachment_form: url missing")
                return attachment

            data_key, data_value = "url", new_url

        else:
            assert False, f"Unhandled attachment type: {new_type}"

        attach_vals = {
            "name": new_name or _("Selection process - Event attachment"),
            "type": new_type,
            "res_model": "civil.service.tracker.process.event",
            "res_id": self.id or 0,
            data_key: data_value,
        }

        _logger.debug(f"_process_attachment_form: values={attach_vals}")

        if self.attachment_id:
            self.attachment_id.write(attach_vals)
            return self.attachment_id
        else:
            new_attachment = Attachment.create(attach_vals)
            values["attachment_id"] = new_attachment.id
            return new_attachment

    @api.model
    def _prevent_selection_process_change(self, values):
        """
        Prevent moving events to a different selection process.

        Raises:
            ValidationError: If any event is being assigned to a process
                             different from its original one.
        """
        if "selection_process_id" in values:
            event_ids = self._ids_to_csv(self)
            process_id = values.get("selection_process_id")
            raise ValidationError(
                f"Event(s) ({event_ids}) cannot be moved to a different "
                f"selection process ({process_id}) than the one they "
                f"originally belonged to."
            )

    @staticmethod
    def _ids_to_csv(record_ids, default="0"):
        """Convert a list of record IDs into a comma-separated string,
        skipping non-integer (new) IDs. Returns a default value if empty.
        """
        if isinstance(record_ids, models.Model):
            record_ids = record_ids.ids

        string_list = [
            str(item_id)
            for item_id in record_ids
            if isinstance(item_id, int)  # Prevents new IDs
        ]

        return ", ".join(string_list) if string_list else default

    def _message_change_thread_to_parent_process(self):
        for record in self:
            record.message_change_thread(record.selection_process_id)

    def _bind_attachments_to_events(self):
        if not self:
            return

        for record in self:
            if record.attachment_id:
                record.attachment_id.write(
                    {
                        "res_model": record._name,
                        "res_field": "attachment_id",
                        "res_id": record.id,
                        "public": True,  # Need to be True to allow it to all users
                    }
                )

    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------

    def quick_create_public_offer(self):
        print("Not implemented!")

    def download_attachment(self):
        self.ensure_one()

        if self.attachment_id:
            result = {
                "type": "ir.actions.act_url",
                "url": self.attachment_url,
                "target": "new",
            }

        else:
            result = {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("No attachment"),
                    "message": _("There is no document linked to this event."),
                    "sticky": False,
                    "type": "warning",
                },
            }

        return result

    # -------------------------------------------------------------------------
    # OVERWRITTEN METHODS
    # -------------------------------------------------------------------------

    @staticmethod
    def _join_event_and_process_name(record):
        parts = [record.name or ""]
        if record.selection_process_id:
            parts.append(record.selection_process_id.display_name)
        return " ― ".join(parts)

    @staticmethod
    def _use_event_name_only(record):
        return record.name

    @api.depends(
        "name",
        "selection_process_id",
        "selection_process_id.display_name",
    )
    @api.depends_context("include_process_in_event_name", "lang")
    def _compute_display_name(self):
        include_proc = bool(
            self.env.context.get("include_process_in_event_name", False)
        )
        if include_proc:
            compose_method = self._join_event_and_process_name
        else:
            compose_method = self._use_event_name_only

        for record in self:
            record.display_name = compose_method(record)
