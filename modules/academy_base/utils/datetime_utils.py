###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from datetime import date, datetime, time, timedelta

from odoo import fields
from odoo.tools.translate import _lt
from pytz import timezone, utc


def now_o_clock(offset_hours=0, round_up=False):
    """Return the current time aligned to an exact hour.

    The current Odoo server datetime is truncated to the beginning of its
    hour. Optionally, it can be rounded up to the next full hour and shifted
    by an additional number of hours.

    Args:
        offset_hours (int | float, optional): Number of hours to add to the
            resulting datetime. Negative values move the result backwards.
            Defaults to 0.
        round_up (bool, optional): If True and the current time is not exactly
            on the hour, move the result to the beginning of the next hour.
            Defaults to False.

    Returns:
        datetime: Naive datetime aligned to a full hour, following Odoo's
        standard server datetime convention.

    Raises:
        TypeError: If ``offset_hours`` cannot be used to build a
        ``timedelta``.
    """
    present = fields.Datetime.now()
    oclock = present.replace(minute=0, second=0, microsecond=0)

    if round_up and (oclock < present):  # almost always
        oclock += timedelta(hours=1)

    return oclock + timedelta(hours=offset_hours)


def get_tz(env):
    """Return the timezone applicable to an Odoo environment.

    The timezone is resolved using the same general priority expected by Odoo:
    first the timezone explicitly supplied in the environment context, then
    the current user's timezone, and finally UTC.

    Args:
        env (odoo.api.Environment): Odoo environment from which the context
            and current user timezone are obtained.

    Returns:
        pytz.tzinfo.BaseTzInfo: Timezone object corresponding to the resolved
        timezone.

    Raises:
        pytz.UnknownTimeZoneError: If the resolved timezone name is not
        recognized by ``pytz``.
    """
    tz_name = env.context.get("tz") or env.user.tz or utc.zone
    return timezone(tz_name)


def localized_dt(value, tz, remove_tz=True):
    """Convert a UTC date or datetime to a target timezone.

    Datetime values without timezone information are interpreted as UTC, in
    accordance with Odoo's convention for stored ``fields.Datetime`` values.
    Timezone-aware datetime values are first converted to UTC and then to the
    requested timezone.

    Date values are interpreted as midnight UTC before conversion. The return
    type follows the input type: a ``datetime`` input returns a ``datetime``,
    while a ``date`` input returns a ``date``.

    Args:
        value (date | datetime): Date or datetime value to convert.
        tz (str | pytz.tzinfo.BaseTzInfo): Target timezone, either as a
            timezone name such as ``"Europe/Madrid"`` or as an existing
            ``pytz`` timezone object.
        remove_tz (bool, optional): If True, remove timezone information from
            a returned datetime after conversion. Has no practical effect on
            date results. Defaults to True.

    Returns:
        date | datetime: Value converted to the target timezone, preserving
        the logical type of the input value.

    Raises:
        TypeError: If ``value`` is neither a ``date`` nor a ``datetime``.
        pytz.UnknownTimeZoneError: If ``tz`` is a string that does not
            identify a valid timezone.
    """
    if isinstance(tz, str):
        tz = timezone(tz)

    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, date):
        dt = datetime.combine(value, time.min)
    else:
        msg = _lt('Given value "{}" is not a valid date or datetime.')
        raise TypeError(msg.format(value))

    if dt.tzinfo is not None:
        dt = dt.astimezone(utc)
    else:
        dt = utc.localize(dt)

    dt = dt.astimezone(tz)

    if remove_tz:
        dt = dt.replace(tzinfo=None)

    if isinstance(value, date) and not isinstance(value, datetime):
        dt = dt.date()

    return dt


def to_datetime(value):
    """Convert a supported value to an Odoo-compatible datetime.

    The conversion is delegated to ``fields.Datetime.to_datetime``, which
    accepts Odoo datetime strings, date objects and datetime objects. Date
    values are converted to midnight.

    Datetime values are expected to be naive, following Odoo's standard
    storage convention.

    Args:
        value (str | date | datetime): Value to convert to a datetime.

    Returns:
        datetime | None: Converted datetime value. Returns None when the
        supplied value is falsy and Odoo treats it as an empty datetime.

    Raises:
        TypeError: If ``value`` has a type that cannot represent an Odoo date
            or datetime value.
        ValueError: If ``value`` has an accepted type but its contents cannot
            be interpreted as a valid date or datetime.
    """
    try:
        return fields.Datetime.to_datetime(value)

    except TypeError as ex:
        msg = _lt('Given value "{}" is not a valid date or datetime type.')
        raise TypeError(msg.format(value)) from ex

    except ValueError as ex:
        msg = _lt(
            'Given value "{}" is not a recognized date or datetime format.'
        )
        raise ValueError(msg.format(value)) from ex


def local_midnight_as_utc(value, from_tz, remove_tz=True):
    """Convert local midnight for a date to its equivalent UTC datetime.

    The supplied value identifies a calendar day. Its time component, when
    present, is discarded and replaced with midnight (00:00:00) in
    ``from_tz``. That local instant is then converted to UTC.

    This is useful when an Odoo ``fields.Datetime`` must represent the start
    of a calendar day in a particular local timezone while being stored using
    Odoo's UTC-based datetime convention.

    Any timezone information already attached to a datetime input is ignored,
    because ``from_tz`` explicitly defines the timezone in which midnight
    must be interpreted.

    Args:
        value (str | date | datetime): Value identifying the calendar day.
            For datetime values, the original time component is ignored.
            String values must use a date or datetime format accepted by
            ``fields.Datetime.to_datetime``.
        from_tz (str | pytz.tzinfo.BaseTzInfo): Timezone in which midnight
            must be interpreted, either as a timezone name such as
            ``"Europe/Madrid"`` or as a ``pytz`` timezone object.
        remove_tz (bool, optional): If True, return a naive UTC datetime
            suitable for Odoo ORM storage. If False, return a timezone-aware
            UTC datetime. Defaults to True.

    Returns:
        datetime: UTC datetime representing midnight in ``from_tz``. The
        result is naive when ``remove_tz`` is True and timezone-aware
        otherwise.

    Raises:
        TypeError: If ``value`` is not a string, date, or datetime.
        ValueError: If a string value cannot be interpreted as a valid date or
            datetime, or if it represents an empty datetime value.
        pytz.UnknownTimeZoneError: If ``from_tz`` is a string that does not
            identify a valid timezone.
        pytz.AmbiguousTimeError: If local midnight is ambiguous because of a
            daylight-saving-time transition.
        pytz.NonExistentTimeError: If local midnight does not exist because of
            a daylight-saving-time transition.
    """
    zero_args = {"hour": 0, "minute": 0, "second": 0, "microsecond": 0}

    if isinstance(from_tz, str):
        from_tz = timezone(from_tz)

    if isinstance(value, datetime):
        naive_midnight = value.replace(tzinfo=None, **zero_args)

    elif isinstance(value, date):
        naive_midnight = datetime.combine(value, time.min)

    elif isinstance(value, str):
        naive_datetime = to_datetime(value)

        if naive_datetime is None:
            msg = _lt('Given value "{}" is not a valid date or datetime.')
            raise ValueError(msg.format(value))

        naive_midnight = naive_datetime.replace(**zero_args)

    else:
        msg = _lt('Given value "{}" is not a valid date, datetime, or string.')
        raise TypeError(msg.format(value))

    aware_midnight = from_tz.localize(naive_midnight, is_dst=None)
    aware_utc_midnight = aware_midnight.astimezone(utc)

    if remove_tz:
        result_dt = aware_utc_midnight.replace(tzinfo=None)
    else:
        result_dt = aware_utc_midnight

    return result_dt
