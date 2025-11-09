# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models
from odoo.exceptions import UserError, ValidationError
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
        field_start (str): Field name representing the date_start of the interval.
        field_stop (str): Field name representing the end of the interval.
        point_in_time (date/datetime/list/tuple): A single date/datetime or a
            tuple/list representing a date_start and end date/datetime for
            comparison.
        trunc_to_date (bool): If True, truncates datetime to date before
            comparison. Defaults to False.

    Returns:
        list: A domain list suitable for Odoo ORM search methods. The domain
        checks if the interval defined by field_start and field_stop overlaps
        with the point in time or interval provided in point_in_time.

    Note:
        - The function handles both single dates/datetime and intervals
        (date_start and end).
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
        msg = _('Invalid external identifier "{}" for help string')
        raise UserError(msg.format(xmlid))

    imd_obj = env["ir.model.data"]
    return imd_obj.xmlid_to_object(xmlid, raise_if_not_found=False)


def single_or_default(items, default=None):
    if items and len(items) == 1 and items[0]:
        return items[0]
    else:
        return default


def get_training_program(env, target):
    """Get the related training program record based on the given target
    record.

    This is useful to get the program from a training ``fields.Reference``
    field.

    Args:
        target (models.Model): A valid Odoo recordset corresponding to the
        target.

    Returns:
        academy.training.program: The related training program record.
    """

    program = env["academy.training.program"]

    if target:
        model = target._name

        if model == "academy.training.action.enrolment":
            program = target.training_action_id.training_program_id
        elif model == "academy.training.action":
            program = target.training_program_id
        elif model == "academy.training.program":
            program = target
        elif model == "academy.competency.unit":
            program = target.training_program_id

    return program


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


def ensure_id(target):
    """Coerce a recordset or id-like value to a single integer id.

    If `target` is an Odoo recordset, ensure it contains exactly one record
    and return its `id`. Otherwise, return `target` unchanged.

    Args:
        target (models.Model | int | Any): Recordset or id-like value.

    Returns:
        int | Any: The record id if a recordset was passed; otherwise the
        original value.

    Raises:
        ValueError: If `target` is a multi-record recordset (raised by
        `ensure_one()`).
    """
    if isinstance(target, models.Model):
        target.ensure_one()
        return target.id

    return target


def ensure_ids(targets, raise_if_empty=True):
    """Coerce a recordset or id(s) into a list of integer ids.

    Behavior:
    - Recordset  -> `recordset.ids`
    - Single int -> `[int]`
    - Other      -> returned as-is (e.g., an existing list/tuple of ids)

    Args:
        targets (models.Model | int | list[int] | tuple[int] | None):
            Source to convert.
        raise_if_empty (bool): If True and `targets` is falsy, raise
            `ValidationError`.

    Returns:
        list[int] | Any: List of ids when conversion applies; otherwise the
        original value.

    Raises:
        ValidationError: When `raise_if_empty` is True and `targets` is falsy.
    """
    if raise_if_empty and not targets:
        raise ValidationError("List of IDs or recordset is expected")

    if isinstance(targets, models.Model):
        return targets.ids

    if isinstance(targets, int):
        return [targets]

    return targets


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalize_m2m(commands):
    ids = set()
    for cmd in commands or []:
        if not isinstance(cmd, (list, tuple)) or not cmd:
            continue
        op = int(cmd[0]) if hasattr(cmd[0], "__int__") else cmd[0]
        if op == 6 and len(cmd) >= 3:
            ids = set(cmd[2] or [])
        elif op == 4 and len(cmd) >= 2:
            ids.add(cmd[1])
        elif op == 3 and len(cmd) >= 2:
            ids.discard(cmd[1])
        elif op == 5:
            ids = set()
    return ids


def _extract_m2m_ids(value):
    """
    Return a set of IDs if `value` plausibly represents an M2M in write-format.
    - Empty cases (None, False, [], ()): return set().
    - List/tuple of ints: return set(ids).
    - List of command tuples:
        * If any op in {0,1,2} → likely O2M → return None (let caller compare raw).
        * If ops subset of {3,4,5,6} → treat as M2M and normalize to set(ids).
    - Otherwise return None (not recognized as M2M shape).
    """
    # Normalize empty representations to empty set
    if value in (None, False):
        return set()

    if isinstance(value, (list, tuple)):
        if not value:
            return set()  # empty sequence → empty M2M

        # Plain list/tuple of ids
        if all(isinstance(x, int) for x in value):
            return set(value)

        # List of command tuples
        if all(isinstance(x, (list, tuple)) and x for x in value):
            ops = {
                int(x[0]) if hasattr(x[0], "__int__") else x[0] for x in value
            }
            if ops & {0, 1, 2}:  # create/update/delete → likely O2M
                return None
            if ops <= {3, 4, 5, 6}:  # unlink/link/clear/set → M2M-compatible
                return _normalize_m2m(value)

    return None


def _is_write_meaningful(field):
    """Stored fields; accept computed only if they have inverse."""
    return getattr(field, "store", False) and (
        not getattr(field, "compute", None) or getattr(field, "inverse", None)
    )


# ---------------------------------------------------------------------------
# Core comparator: write-format vs write-format
# ---------------------------------------------------------------------------


def compare_write_values(left_write, right_write, *, fields):
    """
    Compare two write-format dicts **without** model metadata and return a
    diff map.

    Semantics
    ---------
    - Inputs are assumed to come from ``_convert_to_write`` (or equivalent).
    - Many2one: compared by raw id/False (direct equality).
    - Many2many: if both sides *look like* M2M (either a list of commands using
      only ops {6,5,4,3} or a list/tuple/set of ints), they are compared as
      **sets of IDs** (order-insensitive).
    - One2many: **skipped** on purpose (write-format alone can’t disambiguate
      create/update/delete without model metadata).
    - Other simple types: direct equality.

    Parameters
    ----------
    left_write : dict
    right_write : dict
    fields : Iterable[str]
        Required list/tuple of field names to compare (keyword-only).

    Returns
    -------
    dict
        A mapping of differences: ``{field: (left_value, right_value)}``.
    """
    if not fields:
        message = "{}: 'fields' is required and cannot be empty"
        raise ValueError(message.format("compare_write_values"))

    names = list(dict.fromkeys(fields))  # stable order, no duplicates
    diffs = {}

    for name in names:
        left_value = left_write.get(name)
        right_value = right_write.get(name)

        # Try to treat M2M by shape
        left_ids = _extract_m2m_ids(left_value)
        right_ids = _extract_m2m_ids(right_value)
        if left_ids is not None and right_ids is not None:
            if left_ids != right_ids:
                diffs[name] = (left_ids, right_ids)
            continue  # already compared as M2M

        # For the rest (including M2O and simple types), compare directly
        if left_value != right_value:
            diffs[name] = (left_value, right_value)

    return diffs


# ---------------------------------------------------------------------------
# Wrappers: records → write-format
# ---------------------------------------------------------------------------


def compare_records(source, target, fields=None, deep_o2m=False):
    """
    Convert both records to write-format and delegate to compare_write_values.
    Model metadata is only used here to choose field names; comparison is
    metadata-free. Note: One2many is always excluded from the comparison.
    """
    source.ensure_one()
    target.ensure_one()

    # Campos por defecto: intersección y "razonables"
    if fields is None:
        common_fields = set(source._fields) & set(target._fields)
        field_names = []
        for name in sorted(common_fields):
            field = source._fields[name]
            # Exclude O2M; keep only write-meaningful fields (helper)
            if field.type != "one2many" and _is_write_meaningful(field):
                field_names.append(name)
    else:
        # Respect caller's list but still exclude O2M and non write-meaningful
        field_names = []
        for name in fields:
            if name in source._fields and name in target._fields:
                field = source._fields[name]
                if field.type != "one2many" and _is_write_meaningful(field):
                    field_names.append(name)

    # Nothing to compare → no diffs
    if not field_names:
        return {}

    left_write = source._convert_to_write({n: source[n] for n in field_names})
    right_write = target._convert_to_write({n: target[n] for n in field_names})

    return compare_write_values(left_write, right_write, fields=field_names)


def compare_record_to_write(
    record, desired_write, fields=None, deep_o2m=False
):
    """
    Compare a single Odoo record against a write-format dict and return a diff map.

    Notes
    -----
    - The record side is converted via ``_convert_to_write``.
    - Delegates the actual comparison to ``compare_write_values`` (metadata-free).
    - One2many fields are excluded by design; Many2many are compared as sets of IDs
      when the value shape looks like M2M (command ops in {6,5,4,3} or a list of ints).
    - ``deep_o2m`` is kept for signature parity and is ignored here.

    Parameters
    ----------
    record : odoo.models.Model
        Single record to compare (ensure_one enforced).
    desired_write : dict
        Target values in write-format (as produced by ``_convert_to_write``).
    fields : Iterable[str] | None
        Optional subset of field names. If None, uses the intersection of
        ``desired_write.keys()`` and the model fields.
    deep_o2m : bool
        Ignored. Present only for API parity.

    Returns
    -------
    dict
        A mapping of differences: ``{field: (left_value, right_value)}``.
        Returns an empty dict if there is nothing to compare.
    """
    record.ensure_one()

    if not isinstance(desired_write, dict):
        message = "{}: 'desired_write' must be a dict"
        raise TypeError(message.format("compare_record_to_write"))

    # Candidate field names (preserve caller / desired_write order where applicable)
    if fields is None:
        candidates = [k for k in desired_write.keys() if k in record._fields]
    else:
        candidates = [
            k for k in fields if k in record._fields and k in desired_write
        ]

    # Exclude One2many and keep only write-meaningful fields
    names = []
    for name in candidates:
        field = record._fields[name]
        if field.type != "one2many" and _is_write_meaningful(field):
            names.append(name)

    # Nothing to compare → no diffs
    if not names:
        return {}

    current_write = record._convert_to_write({n: record[n] for n in names})
    return compare_write_values(current_write, desired_write, fields=names)


# ---------------------------------------------------------------------------
# Boolean wrappers
# ---------------------------------------------------------------------------


def are_different(source, target, fields=None, deep_o2m=False):
    """Boolean wrapper around `compare_records`."""
    return bool(
        compare_records(source, target, fields=fields, deep_o2m=deep_o2m)
    )


def are_different_to_write(record, desired_write, fields=None, deep_o2m=False):
    """Boolean wrapper around `compare_record_to_write`.

    Note: `deep_o2m` is ignored in the write-dict path; kept for API parity.
    """
    return bool(
        compare_record_to_write(
            record, desired_write, fields=fields, deep_o2m=deep_o2m
        )
    )
