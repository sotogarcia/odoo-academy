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


def are_different(source, target, fields=None, deep_o2m=False):
    """
    Boolean wrapper around `compare_records`.

    Delegates all comparison semantics to `compare_records` and returns True
    if there are differences, False otherwise.

    Args:
        source (odoo.models.Model): First record (single record).
        target (odoo.models.Model): Second record (single record).
        fields (Iterable[str] | None): Optional subset of field names to compare.
        deep_o2m (bool | str | Callable): See `compare_records`.

    Returns:
        bool: True if differences exist; False otherwise.
    """
    result = compare_records(source, target, fields=fields, deep_o2m=deep_o2m)
    return bool(result)


def compare_records(source, target, fields=None, deep_o2m=False):
    """
    Compare two Odoo records using ORM semantics and return a diffs dict.

    Semantics:
      - Uses `record._convert_to_write()` so Many2one become **ids**
        and X2Many become **fields.Command** lists.
      - Many2many are compared as **sets of IDs** (order-insensitive).
      - One2many handling:
          * deep_o2m == False       → O2M fields are **skipped**.
          * deep_o2m in (True, "ids") → compare **sets of child IDs**.
          * deep_o2m in {str, callable(rec)->hashable} → match children by that
            **key** and compare their shallow payload (no deep diff of children).
      - Only compares fields present on **both** models and considered
        “write-meaningful”: stored fields; computed fields only if they define
        an inverse method.

    Args:
        source (odoo.models.Model): First record (ensure_one).
        target (odoo.models.Model): Second record (ensure_one).
        fields (Iterable[str] | None): Optional subset of field names to compare.
        deep_o2m (bool | str | Callable): O2M comparison mode as above.

    Returns:
        dict: Diffs by field.
            - Simple/M2O/M2M → {field: (left_value, right_value)}
            - O2M-by-key     → {field: {
                                   "added": set,
                                   "removed": set,
                                   "changed": {key: subdiff}
                               }}
    """
    source.ensure_one()
    target.ensure_one()

    # Intersection of field names present on both models
    common_fields = set(source._fields) & set(target._fields)
    if fields is not None:
        common_fields &= set(fields)

    # Keep only "write-meaningful" stored fields
    def _is_write_meaningful(field):
        # Stored fields; accept computed only if they have inverse
        return getattr(field, "store", False) and (
            not getattr(field, "compute", None)
            or getattr(field, "inverse", None)
        )

    field_names = []
    for name in sorted(common_fields):
        field = source._fields[name]
        if field.type == "one2many":
            if deep_o2m:
                field_names.append(name)
        else:
            if _is_write_meaningful(field):
                field_names.append(name)

    # Convert both sides to write-format once
    left_write = source._convert_to_write({k: source[k] for k in field_names})
    right_write = target._convert_to_write({k: target[k] for k in field_names})

    diffs = {}
    for name in field_names:
        field = source._fields[name]
        left_value = left_write.get(name)
        right_value = right_write.get(name)

        if field.type == "many2one":
            # Already ids in write-format; direct compare is fine
            if left_value != right_value:
                diffs[name] = (left_value, right_value)

        elif field.type == "many2many":
            # Compare sets of ids (ignore order / command shapes)
            left_ids = (
                normalize_m2m(left_value)
                if isinstance(left_value, (list, tuple))
                else set(source[name].ids)
            )
            right_ids = (
                normalize_m2m(right_value)
                if isinstance(right_value, (list, tuple))
                else set(target[name].ids)
            )
            if left_ids != right_ids:
                diffs[name] = (left_ids, right_ids)

        elif field.type == "one2many":
            if not deep_o2m:
                continue  # skip O2M entirely

            # Mode A: by ids
            if deep_o2m is True or deep_o2m == "ids":
                source_ids = set(source[name].ids)
                target_ids = set(target[name].ids)
                if source_ids != target_ids:
                    diffs[name] = (source_ids, target_ids)

            else:
                # Mode B: by key (deep_o2m is str key or callable(rec)->hashable)
                key_getter = (
                    (lambda r: getattr(r, deep_o2m))
                    if isinstance(deep_o2m, str)
                    else deep_o2m
                )
                source_by_key = {key_getter(rec): rec for rec in source[name]}
                target_by_key = {key_getter(rec): rec for rec in target[name]}

                added = set(target_by_key) - set(source_by_key)
                removed = set(source_by_key) - set(target_by_key)
                changed = {}

                for child_key in set(source_by_key) & set(target_by_key):
                    subdiff = compare_records(
                        source_by_key[child_key],
                        target_by_key[child_key],
                        fields=None,
                        deep_o2m=False,
                    )
                    if subdiff:
                        changed[child_key] = subdiff

                if added or removed or changed:
                    diffs[name] = {
                        "added": added,
                        "removed": removed,
                        "changed": changed,
                    }

        else:
            # Simple types (char, int, float, boolean, selection, date/datetime, etc.)
            if left_value != right_value:
                diffs[name] = (left_value, right_value)

    return diffs


def normalize_m2m(commands):
    """
    Reduce a sequence of Many2many commands to the resulting set of IDs.
    Supports 6 (set), 4 (link/add), 3 (unlink/remove), 5 (clear).
    Accepts numeric tuples or fields.Command tuples (IntEnum-compatible).
    """
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
