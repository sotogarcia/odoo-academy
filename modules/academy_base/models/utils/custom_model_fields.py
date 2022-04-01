# -*- coding: utf-8 -*-
""" Many2manyThroughView (overload for fields.Many2many)

This module has an Odoo overloaded fields.Many2many with change the middle
TABLE by an SQL VIEW

Todo:
    * Move the SQL outside Many2manyThroughView class to paren models.Model

"""


from logging import getLogger


# pylint: disable=locally-disabled, E0401
from odoo.fields import Many2many, Default
from odoo.tools import sql as sqltools
from odoo.tools.translate import _

# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class Many2manyThroughView(Many2many):
    """ Custom Many2many field, it uses a SQL view as middle
    """

    # pylint: disable=locally-disabled, R0913
    def __init__(self, comodel_name=Default, relation=Default, column1=Default,
                 column2=Default, string=Default, **kwargs):
        """ Constructor overload, it ensures parent constructor will be called
        """

        super(Many2manyThroughView, self).__init__(
            comodel_name=comodel_name,
            relation=relation,
            column1=column1,
            column2=column2,
            string=string,
            **kwargs
        )

    # pylint: disable=locally-disabled, W0613
    def update_db(self, model, columns):
        """ Overload method to create middle relation. This will make
        a new SQL VIEW instead a SQL TABLE.
        """

        # Parent method will never been called
        # super(Many2manyThroughView, self).update_db(model, columns)

        if self._view_can_be_built(model) and \
           self._view_needs_update(model.env.cr):

            self._notify_the_update()
            self._drop_relation_if_exists(model.env.cr)
            self._create_view(model.env.cr)
            self._add_rules(model.env.cr)

    # ------------------------- AUXILIARY METHODS -----------------------------

    def _notify_the_update(self):
        """ Write log message telling SQL VIEW will be created
        instead a TABLE. This message will be shown before the
        proccess starts announcing what is going to be done.
        """

        msg = 'Creating SQL VIEW %s as middle table for %s field'
        _logger.debug(msg, self.relation, self.name)

    def _both_tables_already_exist(self, model):
        ''' Both fields which are involved in relation  calls
        method to create middle table. First filed creates his
        own table and it tries to build middle VIEW but this VIEW
        needs the table of the second involved field. This methos
        checks if one and second table have been already created.
        '''

        sql = '''
            SELECT
                COUNT (*)
            FROM
                information_schema.tables
            WHERE
                TABLE_NAME IN ('{}', '{}');
        '''

        # pylint: disable=locally-disabled, W0212
        table1 = model._table
        table2 = model.env[self.comodel_name]._table

        model.env.cr.execute(sql.format(table1, table2))
        result = model.env.cr.fetchone()

        # If table1 and table2 are the same, the number of retrieved records
        # it must be one, otherwise it must be two.
        items = result[0] if result else 0
        same_table = (table1 == table2)

        return items == 2 or (same_table and items == 1)

    def _view_can_be_built(self, model):
        """ Sometimes update_db method is called whithout required
        arguments, in these cases the update behavior should not be executed
        """

        # If some of the arguments has not been given.
        if not self.relation or not self.column1 or not self.column2:
            pattern = '%s: Some of the arguments has not been given'
            _logger.debug(pattern % model)
            return False

        # If some of the arguments has default value
        if Default in (self.relation, self.column1, self.column2):
            pattern = '%s: Some of the arguments has default value'
            _logger.debug(pattern % model)
            return False

        # OLD :: Relation has a related SQL statement
        # if not getattr(self, self.relation.upper()):
        #     return False

        # Relation has a related SQL statement
        if not hasattr(self, 'sql'):
            _logger.debug('%s: Relation has a related SQL statement' % model)
            return False

        # Left table and right table must exist before VIEW creation
        if not self._both_tables_already_exist(model):
            pattern = _('%s: Left table and right table must exist before '
                        'VIEW creation')
            _logger.debug(pattern % model)
            return False

        return True

    def _get_column_names(self, cursor):
        """ Check the both columns of the view has correct names
        """

        sql = '''
            SELECT
                "column_name" :: VARCHAR AS column1,
                LEAD ("column_name") OVER () :: VARCHAR AS column2
            FROM
                information_schema."columns"
            WHERE
                "table_name" = '{}'
            ORDER BY
                ordinal_position ASC
            LIMIT 1
        '''

        sql = sql.format(self.relation)
        cursor.execute(sql)
        return cursor.fetchone()

    def _column_names_match(self, cursor):
        names = self._get_column_names(cursor)

        return names and self.column1 in names and self.column2 in names

    def _column_order_match(self, cursor):
        names = self._get_column_names(cursor)

        pos1 = names.index(self.column1)
        pos2 = names.index(self.column2)

        return pos1 < pos2

    def _relation_is_actually_a_table(self, cursor):
        """ Check if relation is a table instead a SQL view
        """

        sql = '''
            SELECT
                (pgc.relkind = 'r')::BOOLEAN as IsATable
            FROM
                pg_class AS pgc
            JOIN pg_namespace n ON (n.oid = pgc.relnamespace)
            WHERE
                pgc.relname = '{}'
            AND n.nspname = 'public';
        '''

        sql = sql.format(self.relation)
        cursor.execute(sql)
        result = cursor.fetchone()

        return result and result[0] is True

    def _view_needs_update(self, cursor):
        """ Middle SQL VIEW should be update if required
        argument values has been given and:
            1. VIEW not exists in database
            2. Relation is a TABLE instead a VIEW
            3. VIEW column names not match with field column names
        """
        result = False

        if not sqltools.table_exists(cursor, self.relation):
            result = True
        elif self._relation_is_actually_a_table(cursor):
            result = True
        elif not self._column_names_match(cursor):
            result = True
        elif self._column_order_match(cursor):  # Removes only if col1, col2
            result = True

        return result

    def _drop_relation_if_exists(self, cursor):
        """ Drops middle relation, both if it is a table or a query
        """

        if self._relation_is_actually_a_table(cursor):
            sql = 'DROP TABLE IF EXISTS {};'
            sql = sql.format(self.relation)
            cursor.execute(sql)
        else:
            self._drop_rules(cursor)
            sqltools.drop_view_if_exists(cursor, self.relation)

    def _drop_rules(self, cursor):
        """ Drops rules to INSERT, UPDATE or DELETE in view
        """
        actions = ['INSERT', 'UPDATE', 'DELETE']
        sql = 'DROP RULE IF EXISTS {name} ON {rel} CASCADE;'

        for action in actions:
            name = '{}_on_{}'.format(self.relation, action).lower()
            sql = sql.format(name=name, rel=self.relation)
            cursor.execute(sql)

    def _add_rules(self, cursor):
        """ Adds rules when INSERT, UPDATE or DELETE to prevent Odoo
        breaks on create, write or unlink
        """
        actions = ['INSERT', 'UPDATE', 'DELETE']
        sql = 'CREATE RULE "{name}" AS ON {act} TO "{rel}" DO INSTEAD NOTHING;'

        for action in actions:

            self._drop_rules(cursor)

            name = '{}_on_{}'.format(self.relation, action).lower()
            sql = sql.format(name=name, act=action, rel=self.relation)
            cursor.execute(sql)

    def _create_view(self, cursor):
        """ It gets VIEW select statement from class constant and
        fills the col1 and col2 string arguments in SQL statement whith
        the names of the columns supplied in field definition.

        Secondly, builds SQL statement to create VIEW using relation
        name and previously filled SQL select statement.

        Finally it executes SQL command to create the middle view.
        """

        select_sql = self.sql
        select_sql = select_sql.format(col1=self.column1, col2=self.column2)

        create_sql = 'CREATE VIEW {} AS {};'.format(
            self.relation, select_sql)

        cursor.execute(create_sql)
