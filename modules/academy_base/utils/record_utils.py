# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.osv.expression import TRUE_DOMAIN, FALSE_DOMAIN
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

from datetime import date, datetime
from logging import getLogger


_logger = getLogger(__name__)


# -----------------------------------------------------------------------------
# Use from this module and from outside it:
#
# from ..utils.record_utils import ARCHIVED_DOMAIN
# from odoo.addons.academy_base.utils.record_utils import ARCHIVED_DOMAIN
# -----------------------------------------------------------------------------.

ARCHIVED_DOMAIN = [("active", "!=", True)]
INCLUDE_ARCHIVED_DOMAIN = ["|", ("active", "=", True), ("active", "!=", True)]


def get_active_records(env, expected=None):
    """
    Retrieves active records based on the active model and IDs from the
    provided Odoo environment context.

    Args:
        env (Environment): The Odoo environment
        expected (tuple): List of expected model names. It also supports either
                          the name of the model itself or a set of records for
                          that model as long as the model is unique.

    Returns:
        recordset or None: A recordset of active records based on the
        context's active model, or None if no active model found.
    """

    _logger.debug(f"get_active_records({env}, {expected})")

    context = env.context
    active_model = context.get("active_model", False)

    if isinstance(expected, str):
        expected = [expected]
    elif isinstance(expected, models.Model):
        expected = [expected._name]

    if active_model and (expected is None or active_model in expected):
        record_set = env[active_model]

        active_ids = context.get("active_ids", [])

        if not active_ids:
            active_id = context.get("active_id", None)
            if active_id:
                active_ids = [active_id]

        if active_ids:
            record_set = record_set.browse(active_ids)

    else:
        record_set = None

    _logger.debug(f"get_active_records > {record_set}")

    return record_set


def has_changed(record, field_name):
    """
    Checks if the specified field's value has changed for a given Odoo record.

    This function is designed to be used within @api.onchange decorated methods
    in Odoo models. It compares the current value of a field with its original
    value (before user changes) to determine if the field has changed.

    Args:
        record (recordset): A single Odoo recordset instance.
        field_name (str): Name of the field to check for changes.

    Returns:
        bool: True if the field's value has changed, False otherwise.

    Raises:
        AssertionError: If the provided recordset does not contain the
        specified field.

    Note:
        This function relies on 'record.origin' to access the original values,
        which is only available for records that are already stored in the
        database.
    """

    _logger.debug(f"has_changed({record}, {field_name})")

    record.ensure_one()

    result = False
    if record:
        if record._origin:
            current_value = getattr(record, field_name)
            old_value = getattr(record.origin, field_name)
            result = current_value != old_value
        else:
            result = True

    _logger.debug(f"has_changed > {result}")

    return result


def create_domain_for_ids(field_name, targets, restrictive=True):
    """
    Creates a domain where the specified field contains any of the given IDs.

    This method constructs a search domain for a given field name, ensuring
    the field contains any of the IDs in the targets. Handles different types
    of target inputs (recordset, int, tuple, list) and raises an error for
    unknown formats.

    Args:
        field_name (str): The field name to construct the domain for.
        targets (models.Model/int/tuple/list): Target IDs to include in the
            domain. Can be a recordset, single ID, or list/tuple of IDs.
        restrictive (bool): When targets are empty then if True returns a
            domain that matches nothing (FALSE_DOMAIN), otherwise matches
            everything (TRUE_DOMAIN). Defaults True.

    Returns:
        list: A domain list suitable for Odoo ORM search methods.

    Raises:
        UserError: If the targets parameter is in an unknown format.
    """

    _logger.debug(
        f"create_domain_for_ids({field_name}, {targets}, {restrictive})"
    )

    if isinstance(targets, models.Model):
        targets = targets.ids
    elif isinstance(targets, (int)):
        targets = [targets]
    elif isinstance(targets, (tuple, list)):
        targets = targets
    else:
        msg = _("Unknown data for targets parameter")
        raise UserError(msg)

    if targets:
        domain = [(field_name, "in", targets)]
    elif restrictive:
        domain = FALSE_DOMAIN
    else:
        domain = TRUE_DOMAIN

    _logger.debug(f"create_domain_for_ids > {domain}")

    return domain


def create_domain_for_interval(
    field_start, field_stop, point_in_time, trunc_to_date=False
):
    """
    Creates a domain to find records where a time interval overlaps with a
    given point in time or another interval. This is useful for filtering
    records based on date or datetime fields.

    Args:
        field_start (str): Field name representing the start of the interval.
        field_stop (str): Field name representing the end of the interval.
        point_in_time (date/datetime/list/tuple): A single date/datetime or a
            tuple/list representing a start and end date/datetime for
            comparison.
        trunc_to_date (bool): If True, truncates datetime to date before
            comparison. Defaults to False.

    Returns:
        list: A domain list suitable for Odoo ORM search methods. The domain
        checks if the interval defined by field_start and field_stop overlaps
        with the point in time or interval provided in point_in_time.

    Note:
        - The function handles both single dates/datetime and intervals
        (start and end).
        - If trunc_to_date is True, datetime values are converted to date by
        truncating the time part, which can be useful for date-only
        comparisons.
    """

    _logger.debug(
        f"create_domain_for_interval({field_start}, {field_stop}, "
        f"{point_in_time}, {trunc_to_date})"
    )
    if isinstance(point_in_time, (list, tuple)):
        date_start, date_stop = point_in_time[0], point_in_time[1]
    else:
        date_start, date_stop = point_in_time, point_in_time

    pattern = DATE_FORMAT if trunc_to_date else DATETIME_FORMAT
    if isinstance(date_start, (date, datetime)):
        date_start = date_start.strftime(pattern)
    if isinstance(date_stop, (date, datetime)):
        date_stop = date_stop.strftime(pattern)

    domain = [
        "&",
        (field_start, "<=", date_stop),
        "|",
        (field_stop, ">=", date_start),
        (field_stop, "=", False),
    ]

    _logger.debug(f"create_domain_for_interval > {domain}")

    return domain


def get_by_ref(env, xmlid, raise_if_not_found=False):
    if isinstance(xmlid, (tuple, list)) and len(xmlid) == 2:
        xmlid = ".".join(xmlid)
    elif not isinstance(str):
        msg = _("Invalid external identifier «{}» for help string")
        raise UserError(msg.format(xmlid))

    imd_obj = env["ir.model.data"]
    return imd_obj.xmlid_to_object(xmlid, raise_if_not_found=False)


def single_or_default(items, default=None):
    if items and len(items) == 1 and items[0]:
        return items[0]
    else:
        return default


def get_training_activity(env, target):
    """Get the related training activity record based on the given target
    record.

    This is useful to get the activity from a training ``fields.Reference``
    field.

    Args:
        target (models.Model): A valid Odoo recordset corresponding to the
        target.

    Returns:
        academy.training.activity: The related training activity record.
    """

    activity = env["academy.training.activity"]

    if target:
        model = target._name

        if model == "academy.training.action.enrolment":
            activity = target.training_action_id.training_activity_id
        elif model == "academy.training.action":
            activity = target.training_activity_id
        elif model == "academy.training.activity":
            activity = target
        elif model == "academy.competency.unit":
            activity = target.training_activity_id

    return activity


def ensure_recordset(env, targets, model):
    """
    Ensure that the input `targets` is returned as a recordset for the
    specified model.

    Args:
        env (Environment): The current Odoo environment.
        targets (RecordSet or list): Either a recordset or a list of IDs.
        model (str): The name of the model to which the records belong.

    Returns:
        RecordSet: A recordset of the specified model.

    Behavior:
        - If `targets` is already a recordset, it is returned as-is.
        - If `targets` is a list or tuple of IDs, it is converted into a
          recordset using `browse()`.
        - Otherwise it will be returned and empty `model` recordset.
    """
    target_set = env[model]

    if isinstance(targets, type(target_set)):  # Si ya es un recordset
        target_set = targets
    elif isinstance(targets, (list, tuple)):  # Si es una lista o tupla de IDs
        target_set = target_set.browse(targets)
    elif isinstance(targets, int):  # Si es un único ID
        target_set = target_set.browse(targets)

    return target_set
