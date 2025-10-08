import json
import logging
from typing import Any, Callable, Iterable, Optional

_logger = logging.getLogger(__name__)

_TRUTHY = {"1", "true", "t", "yes", "y", "on"}
_FALSY = {"0", "false", "f", "no", "n", "off"}


def _cast_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    s = str(value).strip().lower()
    if s in _TRUTHY:
        return True
    if s in _FALSY:
        return False
    raise ValueError(f"Not a boolean: {value!r}")


def _cast_json(value: Any) -> Any:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        return value
    return json.loads(value)


def _cast_list(value: Any, sep: str = ",") -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(x) for x in value]
    return [item.strip() for item in str(value).split(sep) if item.strip()]


def get_config_param(
    env,
    name: str,
    cast: Callable[[Any], Any] | str = str,
    default: Any = None,
    *,
    strip: bool = True,
    lower: bool = False,
    choices: Optional[Iterable[Any]] = None,
    validator: Optional[Callable[[Any], None]] = None,
    sep: str = ",",  # used if cast == "list"
    log_errors: bool = True,
) -> Any:
    """
    Read `ir.config_parameter` and return a converted value.

    Args:
        env: Odoo environment.
        name: Parameter key.
        cast: Converter or alias: str|int|float|bool|'json'|'list'.
        default: Value to return on missing/invalid.
        strip: Strip whitespace for str inputs before casting.
        lower: Lowercase for str inputs before casting.
        choices: Allowed set of values (checked after casting).
        validator: Callable(value) -> None (raise on invalid).
        sep: Separator for 'list' casting.
        log_errors: Log warnings on conversion/validation failures.

    Returns:
        Converted value or `default` on error/missing.
    """
    p = env["ir.config_parameter"].sudo()
    raw = p.get_param(name, default)

    # Pre-normalize string input
    if isinstance(raw, str) and strip:
        raw = raw.strip()
    if isinstance(raw, str) and lower:
        raw = raw.lower()

    # Resolve built-in casters
    if cast is bool or cast == bool:
        caster = _cast_bool
    elif cast is int or cast == int:
        caster = int
    elif cast is float or cast == float:
        caster = float
    elif cast == "json":
        caster = _cast_json
    elif cast == "list":
        caster = lambda v: _cast_list(v, sep=sep)
    elif cast is str or cast == str:
        caster = str
    elif callable(cast):
        caster = cast
    else:
        # Unknown caster: return default
        if log_errors:
            _logger.warning("Unknown caster for %s; returning default.", name)
        return default

    # Cast
    try:
        value = caster(raw)
    except Exception as exc:
        if log_errors:
            _logger.warning(
                "Invalid value %r for parameter %s: %s. Using default %r.",
                raw,
                name,
                exc,
                default,
            )
        return default

    # Choices check
    if choices is not None and value not in choices:
        if log_errors:
            _logger.warning(
                "Value %r for %s not in allowed choices %r. Using default %r.",
                value,
                name,
                list(choices),
                default,
            )
        return default

    # External validation hook
    if validator is not None:
        try:
            validator(value)
        except Exception as exc:
            if log_errors:
                _logger.warning(
                    "Value %r for %s failed validation: %s. Using default %r.",
                    value,
                    name,
                    exc,
                    default,
                )
            return default

    return value
