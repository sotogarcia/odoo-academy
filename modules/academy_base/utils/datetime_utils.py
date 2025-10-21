from odoo import fields
from odoo.tools.translate import _lt

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
        msg = _lt('Given value "{}" is not a valid date or datetime.')
        raise ValueError(msg.format(value))

    dt = utc.localize(dt)
    dt = dt.astimezone(tz)

    if remove_tz:
        dt = dt.replace(tzinfo=None)

    if isinstance(value, datetime):
        dt = dt.date()

    return dt


def to_datetime(value):
    try:
        dt_value = fields.Datetime.from_string(value)

    except ValueError:
        try:
            d_value = fields.Date.from_string(value)
            dt_value = datetime.combine(d_value, time.min)

        except ValueError:
            msg = _lt(
                'Given string value "{}" is not a recognized date or datetime format.'
            )
            raise ValueError(msg.format(value))

    return dt_value


def local_midnight_as_utc(value, from_tz, remove_tz=True):
    """Converts a local date/datetime, interpreted as midnight (00:00:00) in
    a specified timezone, to its equivalent Coordinated Universal Time (UTC).

    This utility is essential for storing fields.Datetime values in Odoo that
    use the date widget, ensuring the stored value reflects the start of the
    local day.

    Args:
        value (date | datetime | str): The date or datetime to convert. If a
            datetime or string with time is provided, the time component is
            reset to 00:00:00.
        from_tz (pytz.tzinfo | str): The local timezone (e.g., 'Europe/Madrid')
            from which the midnight moment is calculated.
        remove_tz (bool, optional): If True, returns a naive datetime (without
            timezone info), which is required for Odoo database storage. If
            False, returns an aware UTC datetime object. Defaults to True.

    Returns:
        datetime: The resulting datetime object in UTC (naive or aware, based
        on remove_tz).

    Raises:
        ValueError: If 'value' is not a valid date, datetime, or string format.

    Example Flow (Spain, UTC+2, remove_tz=True):
        1. Input Value: 2025-10-10
        2. Localized: 2025-10-10 00:00:00+02:00
        3. Converted to UTC: 2025-10-09 22:00:00+00:00
        4. Result: 2025-10-09 22:00:00
    """
    zero_args = dict(hour=0, minute=0, second=0, microsecond=0)

    if isinstance(from_tz, str):
        from_tz = timezone(from_tz)

    if isinstance(value, date):
        naive_midnight = datetime.combine(value, time.min)

    elif isinstance(value, datetime):
        naive_midnight = value.replace(**zero_args)

    elif isinstance(value, str):
        naive_datetime = to_datetime(value)
        naive_midnight = naive_datetime.replace(**zero_args)

    else:
        msg = _lt('Given value "{}" is not a valid date, datetime, or string.')
        raise ValueError(msg.format(value))

    aware_midnight = from_tz.localize(naive_midnight)
    aware_utc_midnight = aware_midnight.astimezone(utc)

    if remove_tz:
        result_dt = aware_utc_midnight.replace(tzinfo=None)
    else:
        result_dt = aware_utc_midnight

    return result_dt
