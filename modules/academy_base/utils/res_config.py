###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

import json
from logging import getLogger

_logger = getLogger(__name__)


_TRUTHY = {"1", "true", "t", "yes", "y", "on"}
_FALSY = {"0", "false", "f", "no", "n", "off"}


def _cast_bool(value):
    """Convert a configuration value to a boolean.

    Boolean values are returned unchanged. ``None`` is interpreted as False.
    Other values are converted to strings, stripped of surrounding whitespace
    and compared case-insensitively against the supported truthy and falsy
    representations.

    Args:
        value (Any): Value to convert to a boolean.

    Returns:
        bool: Boolean representation of ``value``.

    Raises:
        ValueError: If ``value`` cannot be recognized as either a truthy or
            falsy boolean representation.
    """
    if isinstance(value, bool):
        return value

    if value is None:
        return False

    normalized = str(value).strip().lower()

    if normalized in _TRUTHY:
        return True

    if normalized in _FALSY:
        return False

    raise ValueError(f"Not a boolean: {value!r}")


def _cast_json(value):
    """Convert a configuration value from JSON when necessary.

    Empty values are converted to None. String values are decoded as JSON,
    while values that are already represented by another Python type are
    returned unchanged.

    Args:
        value (Any): Value to convert from its JSON representation.

    Returns:
        Any: Decoded JSON value, None for empty input, or the original value
        when it is not a string.

    Raises:
        json.JSONDecodeError: If a string value does not contain valid JSON.
    """
    if value is None or value == "":
        return None

    if not isinstance(value, str):
        return value

    return json.loads(value)


def _cast_list(value, sep=","):
    """Convert a configuration value to a list of strings.

    Empty values produce an empty list. Existing lists, tuples and sets are
    converted item by item to strings. Other values are converted to a string
    and split using ``sep``. Empty items produced by splitting are discarded.

    Args:
        value (Any): Value to convert to a list.
        sep (str, optional): Separator used when splitting scalar values.
            Defaults to ``","``.

    Returns:
        list[str]: List containing the string representation of the supplied
        values.

    Raises:
        TypeError: If ``sep`` is neither a string nor None.
        ValueError: If ``sep`` is an empty string.
    """
    if value is None or value == "":
        return []

    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]

    return [item.strip() for item in str(value).split(sep) if item.strip()]


def get_config_param(
    env,
    name,
    cast=str,
    default=None,
    *,
    strip=True,
    lower=False,
    choices=None,
    validator=None,
    sep=",",
    log_errors=True,
):
    """Return a configuration parameter converted to a requested type.

    The parameter is read from ``ir.config_parameter`` using ``sudo()``.
    Missing or empty parameters, as resolved by Odoo's
    ``ir.config_parameter.get_param()``, return ``default`` without applying any
    conversion to the default value.

    String values can optionally be stripped of surrounding whitespace and
    converted to lowercase before casting.

    Supported built-in casters are ``str``, ``int``, ``float`` and ``bool``.
    The special aliases ``"json"`` and ``"list"`` are also supported. Any
    other callable is treated as a custom caster and receives the normalized
    raw parameter value as its only argument.

    After conversion, the value can optionally be restricted to a collection
    of allowed values and validated by a custom callable. Conversion and
    validation failures return ``default`` and can optionally be logged.

    Args:
        env (odoo.api.Environment): Odoo environment used to access
            ``ir.config_parameter``.
        name (str): Technical key of the configuration parameter.
        cast (type | str | callable, optional): Converter to apply to the raw
            parameter value. Supported values are ``str``, ``int``, ``float``,
            ``bool``, ``"json"``, ``"list"``, or a custom callable. Defaults
            to ``str``.
        default (Any, optional): Value returned when the parameter is missing
            or empty according to ``ir.config_parameter.get_param()``,
        strip (bool, optional): If True, remove leading and trailing
            whitespace from string values before conversion. Defaults to True.
        lower (bool, optional): If True, convert string values to lowercase
            before conversion. Defaults to False.
        choices (Iterable | None, optional): Collection of allowed converted
            values. If the converted value is not present, ``default`` is
            returned. The iterable is materialized once before checking
            membership. Defaults to None.
        validator (callable | None, optional): Callable receiving the converted
            value. It should raise an exception when the value is invalid.
            Defaults to None.
        sep (str, optional): Separator used when ``cast`` is ``"list"``.
            Defaults to ``","``.
        log_errors (bool, optional): If True, unsupported casters, conversion
            errors, invalid choices and validation failures are logged as
            warnings. Defaults to True.

    Returns:
        Any: Converted and validated parameter value, or ``default`` when the
        parameter is missing or cannot be accepted.
    """

    parameter_obj = env["ir.config_parameter"].sudo()

    missing = object()
    raw = parameter_obj.get_param(name, missing)

    if raw is missing:
        return default

    if isinstance(raw, str) and strip:
        raw = raw.strip()

    if isinstance(raw, str) and lower:
        raw = raw.lower()

    if cast is bool:
        caster = _cast_bool
    elif cast is int:
        caster = int
    elif cast is float:
        caster = float
    elif cast == "json":
        caster = _cast_json
    elif cast == "list":
        caster = _cast_list
    elif cast is str:
        caster = str
    elif callable(cast):
        caster = cast
    else:
        if log_errors:
            _logger.warning(
                "Unknown caster for parameter %s. Using default %r.",
                name,
                default,
            )

        return default

    try:
        if cast == "list":
            value = caster(raw, sep=sep)
        else:
            value = caster(raw)
    except Exception as exc:  # noqa: BLE001
        if log_errors:
            _logger.warning(
                "Invalid value %r for parameter %s: %s. Using default %r.",
                raw,
                name,
                exc,
                default,
            )

        return default

    if choices is not None:
        allowed_values = tuple(choices)

        if value not in allowed_values:
            if log_errors:
                _logger.warning(
                    "Value %r for parameter %s not in allowed choices %r. "
                    "Using default %r.",
                    value,
                    name,
                    allowed_values,
                    default,
                )

            return default

    if validator is not None:
        try:
            validator(value)
        except Exception as exc:  # noqa: BLE001
            if log_errors:
                _logger.warning(
                    "Value %r for parameter %s failed validation: %s. "
                    "Using default %r.",
                    value,
                    name,
                    exc,
                    default,
                )

            return default

    return value
