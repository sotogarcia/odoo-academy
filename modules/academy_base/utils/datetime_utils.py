from odoo import fields
from odoo.tools.translate import _

from datetime import date, datetime, time, timedelta
from pytz import utc, timezone


def now_o_clock(offset_hours=0, round_up=False):
    present = fields.datetime.now()
    oclock = present.replace(minute=0, second=0, microsecond=0)

    if round_up and (oclock < present):  # almost always
        oclock += timedelta(hours=1)

    return oclock + timedelta(hours=offset_hours)


def get_tz(env):
    tz = env.user.tz or utc.zone
    return timezone(tz)


def localized_dt(value, tz, remove_tz=True):
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, date):
        dt = datetime.combine(value, time.min)
    else:
        msg = _('Given value «{}» is not a valid date or datetime.')
        raise ValueError(msg.format(value))

    dt = utc.localize(dt)
    dt = dt.astimezone(tz)

    if remove_tz:
        dt = dt.replace(tzinfo=None)

    if isinstance(value, datetime):
        dt = dt.date()

    return dt
