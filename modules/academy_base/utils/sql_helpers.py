# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import api, SUPERUSER_ID
from odoo.tools import config

from os import path
from logging import getLogger


_logger = getLogger(__name__)


def search_for_path_in_addons(relative_path, file_name=None):
    result = None

    addons_paths = config['addons_path']

    if addons_paths:
        if isinstance(relative_path, (tuple, list)):
            relative_path = path.sep.join(relative_path)

        if file_name:
            relative_path = path.join(relative_path, file_name)

        for addons_path in addons_paths.split(','):
            file_path = path.join(addons_path, relative_path)
            if path.exists(file_path):
                result = file_path
                break

    return result


def execute_sql_script(cr, relative_path, file_name, referrer='SQL Script'):
    """
    Executes a SQL script file located in the specified relative path. This
    function is designed for use within Odoo modules, either in the same module
    or from external ones.

    Args:
        cr (cursor): Database cursor provided by the Odoo environment.
            relative_path (str/tuple/list): The relative path from the addons
            directory to the SQL file. Can be a string, or a tuple/list of path
            components.
        file_name (str): Name of the SQL file to be executed.
        referrer (str, optional): A string indicating the referrer of the
            script execution, used for logging purposes.
            Defaults to 'SQL Script'.

    Note:
        - This function reads and executes the content of the SQL file.
        - It logs the execution status, including any errors encountered.
        - The function is meant to be versatile, allowing use from different
          modules and supports both string and list/tuple for the relative
          path.
        - Ensure that the SQL script does not contain harmful commands, as it
          will be executed directly in the database.
    """

    env = api.Environment(cr, SUPERUSER_ID, {})

    if isinstance(relative_path, (tuple, list)):
        relative_path = path.sep.join(relative_path)

    file_path = search_for_path_in_addons(relative_path, file_name)

    if file_path:
        try:
            with open(file_path, 'r') as file:
                script = file.read()
                env.cr.execute(script)

            _logger.info(f'{referrer}. Successfully executed {file_name}')

        except Exception as ex:
            _logger.error(f'{referrer}. Error executing {file_name}: {ex}')

    else:
        _logger.warning(f'{referrer}. File not found: {file_name}')


def install_extension(cr, extension):
    """
    Installs the extension in the PostgreSQL database.
    This function should be called with care, preferably during a maintenance
    period, as it requires database superuser privileges.

    Args:
        cr (cursor): Database cursor provided by the Odoo environment.

    Note:
        - This operation requires superuser privileges in the PostgreSQL
          database.
        - Ensure that this script is executed in a controlled environment.
    """

    sql = f'CREATE EXTENSION IF NOT EXISTS {extension};'

    try:
        with api.Environment.manage():
            env = api.Environment(cr, SUPERUSER_ID, {})
            env.cr.execute(sql)
            env.cr.commit()

    except Exception as ex:
        message = f'{extension} could not be installed. System says: {ex}'
        _logger.warning(message)


def process_psql_exception(ex):
    result = {'pgcode': str(ex.pgcode)}

    data = ex.pgerror
    if not data:
        return result

    lines = data.split('\n')
    for line in lines:
        if not line:
            continue

        pos_colon = line.find(': ')
        if pos_colon:
            key = line[:pos_colon].strip().lower()
            value = line[(pos_colon + 1):].strip()
            result.update({key: value})

    return result


def create_index(env, table_name, fields, unique=False):
    """
    Create an index on the specified fields for the given table.

    Args:
        env (Environment): The Odoo environment to execute the SQL query.
        table_name (str): Name of the table where the index will be
            created.
        fields (list or str): The field(s) to index.
        unique (bool): If True, creates a unique index. Default is False.

    Raises:
        ValueError: If table_name or fields are invalid.
    """
    if not table_name or not fields:
        message = 'Table name and fields must be specified and non-empty.'
        raise ValueError(message)

    if isinstance(fields, str):
        fields = [fields]

    unique_str = ' UNIQUE ' if unique else ''
    field_names = '_'.join(fields)
    field_list = ', '.join(fields)

    sentence = (f'CREATE {unique_str} INDEX IF NOT EXISTS '
                f'{table_name}_{field_names}_idx ON {table_name} '
                f'({field_list})')

    try:
        env.cr.execute(sentence)

        message = (f'New {unique_str.strip().lower()} index '
                   f'{table_name}_{field_names}_idx was added to '
                   f'{table_name} table, using {field_list}.')
        _logger.debug(message)

    except Exception as ex:
        message = (f'New {unique_str.strip().lower()} index '
                   f'{table_name}_{field_names}_idx could not be added to '
                   f'{table_name} table, using {field_list}. '
                   f'System says: {ex}')
        _logger.error(message)
