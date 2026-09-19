###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################


from logging import getLogger
from operator import eq, ge, gt, le, lt, ne
from uuid import uuid4

from odoo import models
from odoo.exceptions import ValidationError
from odoo.osv.expression import AND
from odoo.tools import SQL
from odoo.tools.safe_eval import safe_eval
from odoo.tools.translate import _lt

_logger = getLogger(__name__)


INVALID_DOMAIN = _lt("Given domain expression %r is not a valid ORM domain")
INVALID_CTX = _lt("Given context expression %r is not a valid context mapping")

OPERATOR_MAP = {
    "=": eq,
    "!=": ne,
    "<": lt,
    "<=": le,
    ">": gt,
    ">=": ge,
}


def evaluate_domain(recordset, src_domain, default=None, raise_on_fail=True):
    """Evaluate a field domain definition into a valid ORM domain.

    The source domain can be provided as a list, tuple, string expression,
    callable, or ``None``. String expressions are evaluated with ``safe_eval``
    using a minimal evaluation context containing the current Odoo environment
    context. Callables receive ``recordset`` as their only argument.

    Args:
        recordset (odoo.models.Model): Recordset used to provide the Odoo
            environment and passed to callable domain definitions.
        src_domain (list | tuple | str | callable | None): Domain definition to
            evaluate. Lists and tuples are converted to a list, strings are
            evaluated with ``safe_eval``, callables are invoked with
            ``recordset``, and ``None`` leaves the default value unchanged.
        default (list | tuple | None, optional): Fallback value returned when the
            domain cannot be evaluated and ``raise_on_fail`` is False. Defaults
            to None.
        raise_on_fail (bool, optional): If True, raise an exception when the
            domain cannot be evaluated or does not produce a list or tuple. If
            False, return ``default`` instead. Defaults to True.

    Returns:
        list | tuple | None: Evaluated ORM domain. If evaluation fails and
        ``raise_on_fail`` is False, returns ``default``.

    Raises:
        ValueError: If evaluation of a string or callable domain fails and
            ``raise_on_fail`` is True.
        TypeError: If ``src_domain`` has an unsupported type, or if the evaluated
            result is not a list or tuple, and ``raise_on_fail`` is True.
    """

    domain = default

    if isinstance(src_domain, (list, tuple)):
        domain = list(src_domain)

    elif isinstance(src_domain, str):
        try:
            minimal_ctx = {"context": recordset.env.context}
            domain = safe_eval(src_domain, minimal_ctx)
        except (NameError, SyntaxError, TypeError, ValueError) as ex:
            if raise_on_fail:
                raise ValueError(INVALID_DOMAIN % src_domain) from ex
            domain = default

    elif callable(src_domain):
        try:
            domain = src_domain(recordset)
        except Exception as ex:
            if raise_on_fail:
                raise ValueError(INVALID_DOMAIN % src_domain) from ex
            domain = default

    elif src_domain is not None and raise_on_fail:
        raise TypeError(INVALID_DOMAIN % src_domain)

    if domain is not None and not isinstance(domain, (list, tuple)):
        # Ensure a proper domain structure
        if raise_on_fail:
            raise TypeError(INVALID_DOMAIN % src_domain)
        domain = default

    return domain


def evaluate_context(recordset, src_context, default=None, raise_on_fail=True):
    """Evaluate a field context definition into a valid context mapping.

    The source context can be provided as a dictionary, a string expression,
    callable, or ``None``. String expressions are evaluated with ``safe_eval``
    using a minimal evaluation context containing the current Odoo environment
    context. Callables receive ``recordset`` as their only argument.

    Args:
        recordset (odoo.models.Model): Recordset used to provide the Odoo
            environment and passed to callable context definitions.
        src_context (dict | str | callable | None): Context definition to
            evaluate. Dictionaries are used directly, strings are evaluated
            with ``safe_eval``, callables are invoked with ``recordset``, and
            ``None`` leaves the default value unchanged.
        default (dict | None, optional): Fallback value returned when the
            context cannot be evaluated and ``raise_on_fail`` is False.
            Defaults to None.
        raise_on_fail (bool, optional): If True, raise an exception when the
            context cannot be evaluated or does not produce a dictionary. If
            False, return ``default`` instead. Defaults to True.

    Returns:
        dict | None: Evaluated context mapping. If evaluation fails and
        ``raise_on_fail`` is False, returns ``default``.

    Raises:
        ValueError: If evaluation of a string or callable context fails and
            ``raise_on_fail`` is True.
        TypeError: If ``src_context`` has an unsupported type, or if the
            evaluated result is not a dictionary, and ``raise_on_fail`` is
            True.
    """
    context = default

    if isinstance(src_context, dict):
        context = src_context

    elif isinstance(src_context, str):
        # Evaluate with minimal context
        try:
            minimal_ctx = {"context": recordset.env.context}
            context = safe_eval(src_context, minimal_ctx)
        except (NameError, SyntaxError, TypeError, ValueError) as ex:
            if raise_on_fail:
                raise ValueError(INVALID_CTX % src_context) from ex
            context = default

    elif callable(src_context):
        try:
            context = src_context(recordset)
        except Exception as ex:
            if raise_on_fail:
                raise ValueError(INVALID_CTX % src_context) from ex
            context = default
    elif src_context is not None and raise_on_fail:
        raise TypeError(INVALID_CTX % src_context)

    if context is not None and not isinstance(context, dict):
        # Ensure a proper context structure
        if raise_on_fail:
            raise TypeError(INVALID_CTX % src_context)
        context = default

    return context


def _prepare_relational_count(
    parent_set,
    field_name,
    expected_type,
    domain=None,
):
    """Prepare common data required to count relational field records.

    The relational field is validated and its domain and context are resolved.
    The field domain is combined with an optional additional domain supplied
    by the caller, and the comodel is configured with the field context.

    Args:
        parent_set (odoo.models.Model): Recordset containing the parent
            records whose related records must be counted.
        field_name (str): Name of the relational field defined on the parent
            model.
        expected_type (str): Expected Odoo relational field type. Typically
            ``"one2many"`` or ``"many2many"``.
        domain (list | tuple | str | callable | None, optional): Additional
            domain to apply to the related records. Defaults to None.

    Returns:
        tuple: A four-item tuple containing the relational field definition,
        the comodel recordset with the field context applied, the combined
        related-record domain and a dictionary initialized to zero for every
        parent record ID.

    Raises:
        TypeError: If ``field_name`` does not identify a field of
            ``expected_type``, or if the field domain, additional domain or
            field context has an unsupported type.
        ValueError: If a domain or context expression cannot be evaluated.
    """
    field = parent_set._fields.get(field_name)

    if not field or field.type != expected_type:
        raise TypeError(
            f"Field {field_name!r} is not a {expected_type} "
            f"on model {parent_set._name}"
        )

    field_domain = evaluate_domain(
        parent_set,
        field.domain,
        default=[],
    )

    extra_domain = evaluate_domain(
        parent_set,
        domain,
        default=[],
    )

    field_context = evaluate_context(
        parent_set,
        field.context,
        default={},
    )

    comodel = parent_set.env[field.comodel_name].with_context(
        **(field_context or {})
    )

    related_domain = AND(
        [
            field_domain or [],
            extra_domain or [],
        ]
    )

    counts = dict.fromkeys(parent_set.ids, 0)

    return field, comodel, related_domain, counts


def one2many_count(parent_set, o2m_field_name, domain=None):
    """Count matching One2many records for each parent record.

    Related records are counted with a single public ORM ``read_group`` call,
    grouped by the inverse Many2one field. Aggregation is therefore performed
    directly by PostgreSQL.

    The domain and context declared on the One2many field are respected,
    together with any additional domain supplied by the caller. Odoo access
    rights, record rules and ``active_test`` behavior are applied by the ORM.

    Args:
        parent_set (odoo.models.Model): Recordset containing the parent
            records whose related records must be counted.
        o2m_field_name (str): Name of the One2many field defined on the parent
            model.
        domain (list | tuple | str | callable | None, optional): Additional
            domain to apply to the related records. Defaults to None.

    Returns:
        dict[int, int]: Mapping from every parent record ID to the number of
        matching related records. Parents without matching records have a
        count of zero.

    Raises:
        TypeError: If ``o2m_field_name`` is not a One2many field, or if a
            domain or context has an unsupported type.
        ValueError: If a domain or context expression cannot be evaluated.
        odoo.exceptions.AccessError: If the current user cannot read the
            related model or the fields involved in the operation.
    """
    field, comodel, related_domain, counts = _prepare_relational_count(
        parent_set,
        o2m_field_name,
        "one2many",
        domain,
    )

    if not parent_set:
        return counts

    related_domain = AND(
        [
            [(field.inverse_name, "in", parent_set.ids)],
            related_domain,
        ]
    )

    grouped_data = comodel.read_group(
        domain=related_domain,
        fields=[field.inverse_name],
        groupby=[field.inverse_name],
        lazy=False,
    )

    for row in grouped_data:
        parent = row.get(field.inverse_name)

        if parent:
            counts[parent[0]] = row["__count"]

    return counts


def many2many_count(parent_set, m2m_field_name, domain=None):
    """Count matching Many2many records for each parent record.

    The comodel domain is converted into an Odoo query so access rights,
    record rules and context-dependent filtering are preserved. The final
    count is performed directly against the Many2many relation table using
    ``odoo.tools.SQL``.

    PostgreSQL performs the aggregation and returns only one row per parent,
    avoiding materialization of every parent-child relation in Python.

    Args:
        parent_set (odoo.models.Model): Recordset containing the parent
            records whose related records must be counted.
        m2m_field_name (str): Name of the Many2many field defined on the
            parent model.
        domain (list | tuple | str | callable | None, optional): Additional
            domain to apply to the related records. Defaults to None.

    Returns:
        dict[int, int]: Mapping from every parent record ID to the number of
        matching related records. Parents without matching records have a
        count of zero.

    Raises:
        TypeError: If ``m2m_field_name`` is not a Many2many field, or if a
            domain or context has an unsupported type.
        ValueError: If a domain or context expression cannot be evaluated.
        odoo.exceptions.AccessError: If the current user cannot read the
            related model or the fields involved in the operation.
    """
    field, comodel, related_domain, counts = _prepare_relational_count(
        parent_set,
        m2m_field_name,
        "many2many",
        domain,
    )

    if not parent_set:
        return counts

    child_query = comodel._search(related_domain)

    relation_table = SQL.identifier(field.relation)
    parent_column = SQL.identifier(field.column1)
    child_column = SQL.identifier(field.column2)

    sql = SQL(
        """
        SELECT %(parent_column)s, COUNT(*)
          FROM %(relation_table)s
         WHERE %(parent_column)s = ANY(%(parent_ids)s)
           AND %(child_column)s IN %(child_query)s
         GROUP BY %(parent_column)s
        """,
        parent_column=parent_column,
        relation_table=relation_table,
        parent_ids=parent_set.ids,
        child_column=child_column,
        child_query=child_query.subselect(),
    )

    for parent_id, count in parent_set.env.execute_query(sql):
        counts[parent_id] = count

    return counts


def is_debug_mode(env):
    """Check whether the current Odoo context enables a debug mode.

    The ``debug`` context value is normalized to a lowercase string and matched
    against the debug modes commonly used by Odoo, including asset and test
    modes.

    Args:
        env (odoo.api.Environment): Odoo environment whose context is
            inspected.

    Returns:
        bool: True if the context contains a recognized debug value, otherwise
            False.
    """
    debug_val = str(env.context.get("debug", False) or "").lower()
    return debug_val in ("1", "true", "assets", "tests", "debug")


def default_code(env, sequence_code):
    """Generate a default uppercase code from an Odoo sequence.

    The next value of the sequence identified by ``sequence_code`` is
    requested. If the sequence does not exist or does not produce a value, a
    UUID-based fallback code is generated instead. The resulting value is
    always converted to uppercase.

    Args:
        env (odoo.api.Environment): Odoo environment used to access
            ``ir.sequence``.
        sequence_code (str): Technical code identifying the Odoo sequence from
            which the next value must be obtained.

    Returns:
        str: Uppercase code generated from the sequence or, if no sequence
        value is available, from a randomly generated UUID.
    """
    sequence_obj = env["ir.sequence"]

    value = str(sequence_obj.next_by_code(sequence_code) or uuid4().hex)

    return value.upper()


def sanitize_code(values_list, convert_case=None):
    """Sanitize code values contained in one or more value dictionaries.

    The function accepts either a single dictionary or a sequence of
    dictionaries. When a dictionary contains a ``code`` value, surrounding
    whitespace is removed and an optional case transformation is applied.
    Empty strings are replaced with ``None``.

    The supplied dictionaries are modified in place.

    Args:
        values_list (dict | list[dict] | tuple[dict]): Dictionary or sequence
            of dictionaries whose ``code`` values must be sanitized.
        convert_case (str | None, optional): Case transformation to apply after
            stripping whitespace. Supported values are ``"lower"``,
            ``"upper"``, ``"title"`` and ``"swapcase"``. If None, the original
            letter case is preserved. Defaults to None.

    Returns:
        None: The supplied dictionaries are modified in place.

    Raises:
        TypeError: If ``values_list`` is not a dictionary, list or tuple, or if
            one of the items in a sequence is not a dictionary.
        ValueError: If ``convert_case`` contains an unsupported transformation
            name.
        odoo.exceptions.ValidationError: If a non-empty ``code`` value is not a
            string.
    """
    if isinstance(values_list, dict):
        target_list = [values_list]
    elif isinstance(values_list, (tuple, list)):
        target_list = values_list
    else:
        message = "Argument must be a dict, tuple or list, not %s"
        raise TypeError(message % type(values_list))

    case_methods = ("lower", "upper", "title", "swapcase")
    if convert_case is not None and convert_case not in case_methods:
        raise ValueError(
            "Argument 'convert_case' must be one of {}, not {!r}".format(
                ", ".join(case_methods), convert_case
            )
        )

    for values in target_list:
        if not isinstance(values, dict):
            raise TypeError(
                f"Each item in 'values_list' must be a dict, "
                f"not {type(values)}"
            )
        code = values.get("code")
        if code is None or code is False:
            continue

        if isinstance(code, str):
            code = code.strip()
            if code and convert_case in case_methods:
                code = getattr(code, convert_case)()
            values["code"] = code or None
        else:
            message = _lt("Field 'code' must be a string.")
            raise ValidationError(message)


def post_note(recordset, pattern, *args, **kwargs):
    """Post an internal note to the chatter of the given recordset.

    The message body is built from ``pattern`` using ``str.format`` with the
    supplied positional and keyword arguments. If formatting fails, the
    original pattern is posted and the formatting error is written to the log.

    If the recordset is empty, or if it does not support ``message_post``, the
    function returns without posting any message.

    Args:
        recordset (odoo.models.BaseModel): Recordset whose records will receive
            the internal note. The model is expected to inherit from
            ``mail.thread``.
        pattern (str): Message body format string.
        *args: Positional arguments passed to ``str.format``.
        **kwargs: Keyword arguments passed to ``str.format``.

    Returns:
        None: The notes are posted in place and no value is returned.

    Raises:
        odoo.exceptions.AccessError: If the current user does not have
            sufficient access rights to post a message on one of the target
            records.
        odoo.exceptions.UserError: If Odoo rejects the message posting
            operation.
    """
    if not recordset:
        return

    try:
        message = str(pattern).format(*args, **kwargs)
    except (AttributeError, IndexError, KeyError, TypeError, ValueError) as ex:
        _logger.warning("post_note format failed: %s", ex)
        message = str(pattern)

    if not hasattr(recordset, "message_post"):
        _logger.warning(
            "Recordset %s does not support chatter (mail.thread)",
            recordset._name,
        )
        return

    for record in recordset:
        record.message_post(
            body=message,
            message_type="comment",
            subtype_xmlid="mail.mt_note",
        )


def str_ids(targets, *, separator=", ", if_empty=""):
    """Return record identifiers as a separator-joined string.

    The source can be an Odoo recordset, a single integer identifier, or a
    sequence of identifiers. Empty recordsets and sequences return
    ``if_empty``.

    This utility is primarily intended for logging and diagnostic messages
    where a compact textual representation of record identifiers is useful.

    Args:
        targets (odoo.models.BaseModel | int | list | tuple | None): Recordset,
            single record identifier, or sequence of identifiers to convert.
            ``None`` is treated as an empty value.
        separator (str, optional): String used to join multiple identifiers.
            Defaults to ``", "``.
        if_empty (str, optional): Value returned when ``targets`` contains no
            identifiers. Defaults to ``""``.

    Returns:
        str: Identifiers converted to strings and joined with ``separator``,
        or ``if_empty`` when no identifiers are available.

    Raises:
        TypeError: If ``targets`` is not an Odoo recordset, integer, list,
            tuple, or None.
    """
    if targets is None:
        target_items = []

    elif isinstance(targets, models.BaseModel):
        target_items = list(map(str, targets.ids))

    elif isinstance(targets, (tuple, list)):
        target_items = list(map(str, targets))

    elif isinstance(targets, int) and not isinstance(targets, bool):
        target_items = [str(targets)]

    else:
        raise TypeError(
            "Argument 'targets' must be a recordset, int, list, tuple or None, "
            f"not {type(targets)}"
        )

    return separator.join(target_items) if target_items else if_empty
