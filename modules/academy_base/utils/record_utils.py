###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from datetime import date, datetime
from logging import getLogger
from re import match as re_match

from odoo import models
from odoo.exceptions import ValidationError
from odoo.osv.expression import FALSE_DOMAIN, TRUE_DOMAIN
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

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
    """Return the active records defined in the Odoo context.

    The active model is read from ``active_model`` and the target record IDs
    are obtained from ``active_ids`` or, when that value is empty, from
    ``active_id``.

    The optional ``expected`` argument can restrict the accepted active model
    to one or more model names. A recordset can also be supplied, in which
    case its model name is used as the expected model.

    Args:
        env (odoo.api.Environment): Odoo environment whose context contains
            the active model and record identifiers.
        expected (str | list | tuple | odoo.models.BaseModel | None, optional):
            Expected active model name or collection of model names. A
            recordset is interpreted as its model name. If None, any active
            model is accepted. Defaults to None.

    Returns:
        odoo.models.BaseModel | None: Recordset containing the active records,
        an empty recordset of the active model when no active IDs are present,
        or None when the active model is missing or does not match
        ``expected``.

    Raises:
        KeyError: If ``model`` does not exist in the Odoo registry.
    """

    _logger.debug(f"get_active_records({env}, {expected})")

    context = env.context
    active_model = context.get("active_model", False)

    if isinstance(expected, str):
        expected = [expected]
    elif isinstance(expected, models.BaseModel):
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
    """Check whether a field value has changed on a single Odoo record.

    This utility is intended primarily for use inside ``@api.onchange``
    methods. It compares the current field value with the value of the
    corresponding original persisted record.

    New records without an original persisted record are considered changed.

    Args:
        record (odoo.models.BaseModel): Single Odoo record whose field value
            must be checked.
        field_name (str): Name of the field to compare.

    Returns:
        bool: True if the current field value differs from the original value,
        or if the record has no persisted origin. False otherwise.

    Raises:
        ValueError: If ``record`` does not contain exactly one record.
        AttributeError: If ``field_name`` does not exist on the record.
    """

    _logger.debug(f"has_changed({record}, {field_name})")

    record.ensure_one()

    if record._origin:
        current_value = getattr(record, field_name)
        old_value = getattr(record._origin, field_name)
        result = current_value != old_value
    else:
        result = True

    _logger.debug(f"has_changed > {result}")

    return result


def create_domain_for_ids(field_name, targets, restrictive=True):
    """Create a domain matching records whose field contains target IDs.

    The target identifiers can be supplied as an Odoo recordset, a single
    integer ID, or a list or tuple of IDs.

    When no target IDs are provided, the returned domain depends on
    ``restrictive``: a restrictive domain matches no records, while a
    non-restrictive domain matches all records.

    Args:
        field_name (str): Name of the field to include in the domain.
        targets (odoo.models.BaseModel | int | list | tuple): Recordset,
            single record ID, or sequence of record IDs.
        restrictive (bool, optional): If True, empty targets produce
            ``FALSE_DOMAIN``. If False, empty targets produce ``TRUE_DOMAIN``.
            Defaults to True.

    Returns:
        list: Odoo ORM domain matching the supplied target IDs.

    Raises:
        TypeError: If ``targets`` has an unsupported type.
    """
    _logger.debug(
        f"create_domain_for_ids({field_name}, {targets}, {restrictive})"
    )

    if isinstance(targets, models.BaseModel):
        targets = targets.ids

    elif isinstance(targets, int) and not isinstance(targets, bool):
        targets = [targets]

    elif not isinstance(targets, (tuple, list)):
        raise TypeError(
            "Argument 'targets' must be a recordset, int, list or tuple, "
            f"not {type(targets)}"
        )

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
    """Create a domain matching records whose interval overlaps a point or
    interval.

    The target interval is defined by ``field_start`` and ``field_stop``. The
    ``point_in_time`` argument can represent either a single point in time or a
    two-value interval.

    Open-ended target intervals are supported: records whose ``field_stop`` is
    False are considered to continue indefinitely.

    When ``trunc_to_date`` is True, date and datetime values are formatted
    using Odoo's server date format. Otherwise, Odoo's server datetime format
    is used.

    Args:
        field_start (str): Name of the field containing the beginning of the
            target interval.
        field_stop (str): Name of the field containing the end of the target
            interval.
        point_in_time (date | datetime | list | tuple): Single date or
            datetime, or a two-item list or tuple containing the beginning and
            end of the interval to compare.
        trunc_to_date (bool, optional): If True, format date and datetime
            values using Odoo's server date format. If False, use the server
            datetime format. Defaults to False.

    Returns:
        list: Odoo ORM domain matching records whose interval overlaps the
        supplied point or interval.

    Raises:
        ValueError: If ``point_in_time`` is a list or tuple that does not
            contain exactly two values.
    """

    _logger.debug(
        f"create_domain_for_interval({field_start}, {field_stop}, "
        f"{point_in_time}, {trunc_to_date})"
    )
    if isinstance(point_in_time, (list, tuple)):
        if len(point_in_time) != 2:
            raise ValueError("'point_in_time' must contain exactly two values")
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
    """Return the record referenced by an external identifier.

    The external identifier can be supplied directly as a string using the
    standard ``"module.name"`` format, or as a two-item tuple or list
    containing the module and identifier name separately.

    Resolution is delegated to ``env.ref``.

    Args:
        env (odoo.api.Environment): Odoo environment used to resolve the
            external identifier.
        xmlid (str | tuple | list): External identifier expressed as
            ``"module.name"`` or as a two-item sequence containing the module
            and identifier name.
        raise_if_not_found (bool, optional): If True, raise an exception when
            the external identifier cannot be resolved. If False, return None.
            Defaults to False.

    Returns:
        odoo.models.BaseModel | None: Referenced Odoo record, or None when it
        cannot be resolved and ``raise_if_not_found`` is False.

    Raises:
        TypeError: If ``xmlid`` is not a string, tuple or list, or if a tuple
            or list does not contain exactly two items.
        ValueError: If the external identifier cannot be resolved and
            ``raise_if_not_found`` is True.
    """
    if isinstance(xmlid, (tuple, list)):
        if len(xmlid) != 2:
            raise TypeError(
                "External identifier must contain exactly a module and a name"
            )

        xmlid = ".".join(xmlid)

    elif not isinstance(xmlid, str):
        raise TypeError(
            f"External identifier must be a string, tuple or list, "
            f"not {type(xmlid)}"
        )

    return env.ref(
        xmlid,
        raise_if_not_found=raise_if_not_found,
    )


def single_or_default(items, default=None):
    """Return the single truthy item in a collection or a default value.

    The first item is returned only when the collection contains exactly one
    element and that element is truthy. In every other case, ``default`` is
    returned.

    Args:
        items (Sequence | None): Collection whose single item must be
            retrieved. Falsy values are treated as empty input.
        default (Any, optional): Value returned when ``items`` does not contain
            exactly one truthy element. Defaults to None.

    Returns:
        Any: The only truthy item in ``items``, or ``default`` otherwise.

    Raises:
        TypeError: If ``items`` is truthy but does not support ``len()`` or
            indexed access.
    """
    if items and len(items) == 1 and items[0]:
        return items[0]

    return default


def get_training_program(env, target):
    """Return the training program associated with a supported target record.

    The related training program is resolved according to the target model.
    Supported models include training action enrolments, training actions,
    training programs and competency units.

    If ``target`` is empty or its model is not supported, an empty
    ``academy.training.program`` recordset is returned.

    Args:
        env (odoo.api.Environment): Odoo environment used to obtain the
            training program model.
        target (odoo.models.BaseModel): Target recordset from which the
            related training program must be resolved.

    Returns:
        odoo.models.BaseModel: Related ``academy.training.program`` recordset,
        or an empty recordset when no related program can be determined.

    Raises:
        ValueError: If ``target`` contains more than one record.
    """

    program = env["academy.training.program"]

    if target:
        target.ensure_one()

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
    """Return the given targets as a recordset of the specified model.

    Existing recordsets are returned unchanged when they belong to the
    expected model. Integer identifiers and sequences of identifiers are
    converted into recordsets using ``browse()``. ``None`` and ``False`` are
    treated as empty values and return an empty recordset.

    Args:
        env (odoo.api.Environment): Odoo environment used to access the target
            model.
        targets (odoo.models.BaseModel | int | list | tuple | None): Existing
            recordset, single record identifier, sequence of identifiers, or
            empty value to convert.
        model (str): Technical name of the expected Odoo model.

    Returns:
        odoo.models.BaseModel: Recordset belonging to ``model``.

    Raises:
        KeyError: If ``model`` does not exist in the Odoo registry.
        TypeError: If ``targets`` is a recordset of a different model or has
            an unsupported type.
    """
    target_set = env[model]

    if targets is None or targets is False:
        return target_set

    if isinstance(targets, models.BaseModel):
        if targets._name != model:
            raise TypeError(
                f"Expected recordset of model {model!r}, "
                f"got {targets._name!r}"
            )

        return targets

    if isinstance(targets, int) and not isinstance(targets, bool):
        return target_set.browse(targets)

    if isinstance(targets, (list, tuple)):
        return target_set.browse(targets)

    raise TypeError(
        "Argument 'targets' must be a recordset, int, list, tuple or None, "
        f"not {type(targets)}"
    )


def ensure_id(target):
    """Return the identifier of a single recordset or the original value.

    If ``target`` is an Odoo recordset, it must contain exactly one record and
    its ``id`` is returned. Values that are not recordsets are returned
    unchanged.

    Args:
        target (odoo.models.BaseModel | Any): Recordset or arbitrary value to
            normalize.

    Returns:
        int | Any: Record identifier when ``target`` is a recordset, otherwise
        the original value.

    Raises:
        ValueError: If ``target`` is an Odoo recordset that does not contain
            exactly one record.
    """

    if isinstance(target, models.BaseModel):
        target.ensure_one()
        return target.id

    return target


def ensure_ids(targets, raise_if_empty=True):
    """Return record identifiers in a normalized form.

    Odoo recordsets are converted to their ``ids`` list and a single integer
    identifier is converted to a one-item list. Other values are returned
    unchanged.

    When ``raise_if_empty`` is True, falsy input values are rejected.

    Args:
        targets (odoo.models.BaseModel | int | list | tuple | None): Recordset,
            single record identifier, collection of identifiers, or another
            value to normalize.
        raise_if_empty (bool, optional): If True, raise a validation error when
            ``targets`` is falsy. Defaults to True.

    Returns:
        list[int] | tuple | None | Any: List of identifiers when ``targets`` is
        a recordset or integer, otherwise the original value.

    Raises:
        odoo.exceptions.ValidationError: If ``raise_if_empty`` is True and
            ``targets`` is falsy.
    """

    if raise_if_empty and not targets:
        raise ValidationError("List of IDs or recordset is expected")

    if isinstance(targets, models.BaseModel):
        return targets.ids

    if isinstance(targets, int) and not isinstance(targets, bool):
        return [targets]

    return targets


def update_target(env, context_key, new_value):
    """Update a record field from a target specification stored in context.

    The context value identified by ``context_key`` must use the format
    ``"model,numeric_ID,field"``. The referenced record and field are
    validated before writing the supplied value.

    If ``new_value`` is an Odoo recordset, it must contain exactly one record
    and its identifier is written instead of the recordset itself.

    Args:
        env (odoo.api.Environment): Odoo environment used to resolve the
            target model and record.
        context_key (str): Context key containing the target specification.
        new_value (Any): Value to write to the target field. A single-record
            Odoo recordset is converted to its record ID.

    Returns:
        odoo.models.BaseModel | None: Updated target recordset, or None when
        the context does not contain a target specification.

    Raises:
        ValidationError: If the target specification is not a string, has an
            invalid format, references an unknown model, references a missing
            record, or identifies a field that does not exist.
        ValueError: If ``new_value`` is an Odoo recordset that does not
            contain exactly one record.
        odoo.exceptions.AccessError: If the current user does not have
            sufficient rights to write the target record.
        odoo.exceptions.UserError: If Odoo rejects the write operation.
    """
    target_spec = env.context.get(context_key)

    if not target_spec:
        return None

    if not isinstance(target_spec, str):
        raise ValidationError(
            env._("The target is not a valid string in the context.")
        )

    pattern = r"^([^,]+),(\d+),([^,]+)$"
    match = re_match(pattern, target_spec)

    if not match:
        raise ValidationError(
            env._(
                "The target specification format is incorrect. "
                "It must be 'model,numeric_ID,field'."
            )
        )

    res_model, res_id_str, res_field = match.groups()
    res_id = int(res_id_str)

    if res_model not in env:
        raise ValidationError(
            env._("The model '{}' does not exist.").format(res_model)
        )

    record = env[res_model].browse(res_id)

    if not record.exists():
        raise ValidationError(
            env._("The record with ID {} in model {} does not exist.").format(
                res_id, res_model
            )
        )

    if res_field not in record._fields:
        raise ValidationError(
            env._("The field '{}' does not exist in model '{}'.").format(
                res_field,
                res_model,
            )
        )

    if isinstance(new_value, models.BaseModel):
        new_value.ensure_one()
        write_values = {res_field: new_value.id}
    else:
        write_values = {res_field: new_value}

    record.write(write_values)

    return record
