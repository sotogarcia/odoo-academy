# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _

from pytz import timezone, utc
from datetime import datetime, timedelta
from logging import getLogger


_logger = getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    """Module configuration attributes"""

    _inherit = ["res.config.settings"]

    teacher_report_type = fields.Selection(
        string="Format",
        required=True,
        readonly=False,
        index=False,
        default="html",
        help="Set how the schedule will be served, by default, to teachers",
        selection=[("pdf", "PDF document"), ("html", "Web page")],
        config_parameter="academy_timesheets.teacher_report_type",
    )

    teacher_report_download = fields.Boolean(
        string="Download",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=_(
            "If set to TRUE the report will be downloaded instead of "
            "displayed in the browser."
        ),
        config_parameter="academy_timesheets.teacher_report_download",
    )

    schedule_for_next_week_from = fields.Selection(
        string="Weekday",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Display the schedule for the following week",
        selection=[
            ("ISO5", "Friday"),
            ("ISO6", "Saturday"),
            ("ISO7", "Sunday"),
        ],
        config_parameter="academy_timesheets.schedule_for_next_week_from",
    )

    schedule_for_next_week_from_time = fields.Float(
        string="Time (UTC)",
        required=False,
        readonly=False,
        index=False,
        default=14.0,
        digits=(16, 2),
        help=(
            "Time from which the schedule of the following week will be "
            "shown"
        ),
        config_parameter="academy_timesheets.schedule_for_next_week_from_time",
    )

    @api.onchange("schedule_for_next_week_from_time")
    def _onchange_schedule_for_next_week_from_time(self):
        max_time = timedelta(hours=23, minutes=59)
        float_max = max_time.total_seconds() / 3600.0

        for record in self:
            old_value = record.schedule_for_next_week_from_time
            new_value = min(float_max, max(0.0, old_value))

            if old_value != new_value:
                record.schedule_for_next_week_from_time = new_value

    wait_to_fill = fields.Float(
        string="Waiting time",
        required=True,
        readonly=False,
        index=False,
        default=0.01666666,
        digits=(16, 8),
        config_parameter="academy_timesheets.wait_to_fill",
        help=(
            "Time during which the information of the last created session "
            "will be kept"
        ),
    )

    help_to_fill = fields.Boolean(
        string="Help to fill",
        required=False,
        readonly=False,
        index=False,
        default=False,
        config_parameter="academy_timesheets.help_to_fill",
        help="Create upcoming sessions for a teacher with the same information",
    )

    teacher_shift_lookback_days = fields.Integer(
        string="Shift lookback days",
        required=True,
        readonly=False,
        index=False,
        default=45,
        help=(
            "Specifies the number of days in the past from which to "
            "calculate shift information."
        ),
        config_parameter="academy_timesheets.teacher_shift_lookback_days",
    )

    _sql_constraints = [
        (
            "teacher_shift_range",
            """CHECK(
                teacher_shift_lookback_days >=7
                AND teacher_shift_lookback_days <= 400
            )""",
            "Shift lookback days must be 7 to 400.",
        )
    ]

    # @api.model
    # def _get_timezone_offset(self):
    #     tz = self.env.user.tz or utc.zone
    #     tz = timezone(tz)
    #     return tz.fromutc(datetime.now()).utcoffset()

    # @staticmethod
    # def _safe_cast(val, to_type, default=None):
    #     """ Performs a safe cast between `val` type to `to_type`
    #     """

    #     try:
    #         return to_type(val)
    #     except (ValueError, TypeError):
    #         return default

    # def _get_next_week_from_time(self):
    #     param_name = 'academy_timesheets.schedule_for_next_week_from_time'
    #     param_obj = self.env['ir.config_parameter'].sudo()
    #     return param_obj.get_param(param_name, default=0.0)

    # def _set_next_week_from_time(self, value):
    #     param_name = 'academy_timesheets.schedule_for_next_week_from_time'
    #     param_obj = self.env['ir.config_parameter'].sudo()
    #     param_obj.set_param(param_name, value)

    # def _update_time_zone(self, param_value, saving=False):

    #     param_value = self._safe_cast(param_value, float, 0.0)
    #     tz_offset = self._get_timezone_offset()

    #     from_time = timedelta(seconds=param_value * 3600.0)
    #     if saving:
    #         from_time -= tz_offset
    #     else:
    #         from_time += tz_offset

    #     return from_time.total_seconds() / 3600.0

    # @api.model
    # def get_values(self):
    #     parent = super(ResConfigSettings, self)
    #     result = parent.get_values()

    #     value = self._get_next_week_from_time()
    #     value = self._update_time_zone(value, saving=False)
    #     result['schedule_for_next_week_from_time'] = float(value)

    #     return result

    # def set_values(self):

    #     value = self.schedule_for_next_week_from_time or 0.0
    #     value = self._update_time_zone(value, saving=True)
    #     self._set_next_week_from_time(value)

    #     parent = super(ResConfigSettings, self)

    #     return parent.set_values()
