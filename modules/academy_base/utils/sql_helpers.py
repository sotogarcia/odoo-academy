###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from logging import getLogger
from os import path

from odoo.tools import SQL, file_path
from odoo.tools.sql import (
    create_index as odoo_create_index,
)
from odoo.tools.sql import (
    create_unique_index as odoo_create_unique_index,
)
from odoo.tools.sql import (
    index_exists,
    make_identifier,
)

_logger = getLogger(__name__)


def search_for_path_in_addons(relative_path, file_name=None):
    """Return the absolute path of a file located in an Odoo addons path.

    The relative path can be supplied either as a string or as a sequence of
    path components. When ``file_name`` is provided, it is appended to the
    relative path before resolving it through Odoo's addons paths.

    Args:
        relative_path (str | list | tuple): Relative path inside an Odoo
            addons directory, or a sequence containing its path components.
        file_name (str | None, optional): File name to append to the relative
            path. Defaults to None.

    Returns:
        str | None: Absolute path of the resolved file or directory, or None
        when it cannot be found.

    Raises:
        TypeError: If the supplied path components cannot be joined.
    """
    if isinstance(relative_path, (tuple, list)):
        relative_path = path.join(*relative_path)

    if file_name:
        relative_path = path.join(relative_path, file_name)

    try:
        return file_path(relative_path)
    except FileNotFoundError:
        return None


def execute_sql_script(env, relative_path, file_name, referrer="SQL Script"):
    """Execute an SQL script stored inside an Odoo addons path.

    The script file is resolved relative to the configured Odoo addons paths,
    read using UTF-8 encoding and executed using the current environment
    cursor.

    Args:
        env (odoo.api.Environment): Odoo environment whose database cursor is
            used to execute the script.
        relative_path (str | list | tuple): Relative directory containing the
            SQL script, or a sequence containing its path components.
        file_name (str): Name of the SQL script file.
        referrer (str, optional): Description used in log messages to identify
            the caller. Defaults to ``"SQL Script"``.

    Returns:
        None: The script is executed in the current Odoo transaction.

    Raises:
        FileNotFoundError: If the SQL script cannot be found.
        OSError: If the script file cannot be read.
    """
    script_path = search_for_path_in_addons(relative_path, file_name)

    if not script_path:
        raise FileNotFoundError(f"{referrer}. File not found: {file_name}")

    with open(script_path, "r", encoding="utf-8") as file:
        script = file.read()

    env.cr.execute(script)

    _logger.info(
        "%s. Successfully executed %s",
        referrer,
        file_name,
    )


def process_psql_exception(ex):
    """Convert PostgreSQL exception information into a dictionary.

    The PostgreSQL error code is stored under ``pgcode``. When PostgreSQL
    provides a textual error message, lines using the ``"key: value"`` format
    are also extracted and normalized to lowercase keys.

    Args:
        ex (Exception): PostgreSQL exception exposing ``pgcode`` and optionally
            ``pgerror`` attributes.

    Returns:
        dict: Dictionary containing the PostgreSQL error code and any parsed
        error properties available in the exception message.
    """
    result = {
        "pgcode": str(getattr(ex, "pgcode", None)),
    }

    data = getattr(ex, "pgerror", None)

    if not data:
        return result

    for line in data.splitlines():
        key, separator, value = line.partition(": ")

        if separator:
            result[key.strip().lower()] = value.strip()

    return result


def create_index(
    env,
    table_name,
    fields,
    unique=False,
    name=None,
    where=None,
    method="btree",
):
    """Create a database index unless an index with the same name exists.

    Standard indexes are created using Odoo's SQL utilities. Unique indexes
    without a partial condition use Odoo's ``create_unique_index`` helper.
    Partial unique indexes, which are not directly supported by that helper,
    are created using Odoo's composable ``SQL`` wrapper.

    Field values are treated as SQL expressions, following the behavior of
    Odoo's standard index helpers. When expressions are used, an explicit
    index name should be supplied.

    Field expressions and the ``where`` predicate are treated as trusted SQL
    fragments and must therefore be defined by application code, not supplied
    directly from untrusted user input.

    Args:
        env (odoo.api.Environment): Odoo environment whose database cursor is
            used to create the index.
        table_name (str): Name of the database table on which the index must
            be created.
        fields (str | list | tuple): Field name, SQL expression, or sequence
            of field names or SQL expressions to include in the index.
        unique (bool, optional): If True, create a unique index. Defaults to
            False.
        name (str | None, optional): Explicit index name. When omitted, a name
            is generated from the table and indexed fields. Defaults to None.
        where (str | None, optional): Trusted SQL predicate used to create a
            partial index. Defaults to None.
        method (str, optional): PostgreSQL index access method. Defaults to
            ``"btree"``.

    Returns:
        None: The index is created in the current Odoo transaction when it
            does not already exist.

    Raises:
        TypeError: If ``fields`` is not a string, list or tuple, or contains
            values that are not strings.
        ValueError: If ``table_name`` or ``fields`` is empty, an index name
            cannot be generated safely, or a unique index requests an access
            method other than ``btree``.
    """
    if not table_name:
        raise ValueError("Table name must be specified and non-empty.")

    if isinstance(fields, str):
        fields = [fields]
    elif isinstance(fields, (list, tuple)):
        fields = list(fields)
    else:
        raise TypeError(
            "Argument 'fields' must be a string, list or tuple, "
            f"not {type(fields)}"
        )

    if not fields:
        raise ValueError("At least one field must be specified.")

    if not all(isinstance(field, str) and field for field in fields):
        raise TypeError("Every indexed field or expression must be a string.")

    if unique and method != "btree":
        raise ValueError("Unique indexes require the 'btree' access method.")

    if name:
        index_name = name
    else:
        if any(not field.isidentifier() for field in fields):
            raise ValueError(
                "Provide 'name' when fields contain SQL expressions."
            )

        field_names = "_".join(fields)
        suffix = "pindex" if where else "index"
        index_name = make_identifier(f"{table_name}_{field_names}_{suffix}")

    if unique and where:
        if index_exists(env.cr, index_name):
            return

        sql = SQL(
            "CREATE UNIQUE INDEX %s ON %s (%s) WHERE %s",
            SQL.identifier(index_name),
            SQL.identifier(table_name),
            SQL(", ").join(SQL(field) for field in fields),
            SQL(where),
        )
        env.cr.execute(sql)

    elif unique:
        odoo_create_unique_index(
            env.cr,
            index_name,
            table_name,
            fields,
        )

    else:
        odoo_create_index(
            env.cr,
            index_name,
            table_name,
            fields,
            method=method,
            where=where or "",
        )

    _logger.debug(
        "Index %s was ensured on table %s using (%s)",
        index_name,
        table_name,
        ", ".join(fields),
    )
