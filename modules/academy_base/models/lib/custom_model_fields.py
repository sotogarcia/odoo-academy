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

            self._notify_the_update() # in log
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

        return result and result[0] == 2


    def _view_can_be_built(self, model):
        """ Sometimes update_db method is called whithout required
        arguments, in these cases the update behavior should not be executed
        """

        # If some of the arguments has not been given.
        if not self.relation or not self.column1 or not self.column2:
            _logger.debug('%s: Some of the arguments has not been given' % model)
            return False

        # If some of the arguments has default value
        if Default in (self.relation, self.column1, self.column2):
            _logger.debug('%s: Some of the arguments has default value' % model)
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
            _logger.debug('%s: Left table and right table must exist before VIEW creation' % model)
            return False

        return True


    def _column_names_match(self, cursor):
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
            LIMIT 1
        '''

        sql = sql.format(self.relation)
        cursor.execute(sql)
        result = cursor.fetchone()

        return result and self.column1 in result and self.column2 in result


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

        #select_sql = getattr(self, self.relation.upper())
        select_sql = self.sql
        select_sql = select_sql.format(col1=self.column1, col2=self.column2)

        create_sql = 'CREATE VIEW {} AS {};'.format(
            self.relation, select_sql)

        cursor.execute(create_sql)


# ------------- SQL STATEMENTS WILL BE USED IN VIEW DEFINITIONS ---------------


TRAINING_MODULE_IDS_SQL = """
    SELECT
        atv."id" AS training_activity_id,
        atm."id" AS training_module_id
    FROM academy_training_activity AS atv
    INNER JOIN academy_competency_unit AS acu
        ON atv."id" = acu.training_activity_id
    INNER JOIN academy_training_module AS atm
        ON acu.training_module_id = atm."id"
"""

TRAINING_UNIT_IDS_SQL = """
    SELECT
        atv."id" AS training_activity_id,
        COALESCE(atu."id", atm."id")::INTEGER AS training_unit_id
    FROM
        academy_training_activity AS atv
    INNER JOIN academy_competency_unit AS acu
        ON atv."id" = acu.training_activity_id
    INNER JOIN academy_training_module AS atm
        ON acu.training_module_id = atm."id"
    LEFT JOIN academy_training_module AS atu
        ON atm."id" = atu.training_module_id
"""

MODULE_INHERITED_RESOURCES_REL = """
    SELECT DISTINCT
        tree.requested_module_id AS training_module_id,
        rel.training_resource_id
    FROM
        academy_training_module_tree_readonly AS tree
    INNER JOIN academy_training_module_training_resource_rel AS rel
        ON tree."responded_module_id" = rel.training_module_id
"""

ACTIVITY_INHERITED_RESOURCES_REL = """
    WITH inherited_resources AS (
        SELECT
            atv."id" AS training_activity_id,
            atr."id" AS training_resource_id
        FROM
            academy_training_activity AS atv
        INNER JOIN academy_competency_unit AS acu
            ON atv."id" = acu.training_activity_id
        INNER JOIN academy_training_module AS atm
            ON acu.training_module_id = atm."id"
        LEFT JOIN academy_training_module AS atu
            ON atm."id" = atu.training_module_id or atm."id" = atu."id"
        INNER JOIN academy_training_module_training_resource_rel AS rel
            ON COALESCE (atu."id", atm."id") = rel.training_module_id
        LEFT JOIN academy_training_resource AS atr
            ON rel.training_resource_id = atr."id"
    )
    SELECT
        training_activity_id,
        training_resource_id
    FROM
        academy_training_activity_training_resource_rel AS rel
    UNION ALL (
        SELECT
            training_activity_id,
            training_resource_id
        FROM
            inherited_resources
    )
"""

ACTION_INHERITED_RESOURCES_REL = """
    WITH module_resources AS (
        SELECT
                atv."id" AS training_activity_id,
                atr."id" AS training_resource_id
        FROM
                academy_training_activity AS atv
        INNER JOIN academy_competency_unit AS acu
                ON atv."id" = acu.training_activity_id
        INNER JOIN academy_training_module AS atm
                ON acu.training_module_id = atm."id"
        LEFT JOIN academy_training_module AS atu
                ON atm."id" = atu.training_module_id or atm."id" = atu."id"
        INNER JOIN academy_training_module_training_resource_rel AS rel
                ON COALESCE (atu."id", atm."id") = rel.training_module_id
        LEFT JOIN academy_training_resource AS atr
                ON rel.training_resource_id = atr."id"
    ), activity_resources AS (
        SELECT
            training_activity_id,
            training_resource_id
        FROM
            academy_training_activity_training_resource_rel AS rel
        UNION ALL (
            SELECT
                training_activity_id,
                training_resource_id
            FROM
                module_resources
        )
    ), inherited_recources AS (
        SELECT
            atc."id" as training_action_id,
            ars.training_resource_id
        FROM
            activity_resources AS ars
        INNER JOIN academy_training_action atc
            ON ars.training_activity_id = atc.training_activity_id

    ) SELECT
        training_action_id,
        training_resource_id
    FROM
            academy_training_action_training_resource_rel AS rel
    UNION ALL (
        SELECT
            training_action_id,
            training_resource_id
        FROM
            inherited_recources
    )
"""



ACTION_EHROLMENT_INHERITED_RESOURCES_REL = """
WITH module_test AS (
    -- Tests in related modules
    SELECT DISTINCT
                rel2.action_enrolment_id as enrolment_id,
        rel.training_resource_id
    FROM
        academy_training_module_tree_readonly AS tree
    INNER JOIN academy_training_module_training_resource_rel AS rel
        ON tree."responded_module_id" = rel.training_module_id
    INNER JOIN academy_action_enrolment_training_module_rel AS rel2
        ON tree.requested_module_id = rel2.training_module_id
), action_test AS (
    -- Tests in action
    SELECT
        tae."id" as enrolment_id,
        rel.training_resource_id
    FROM
        academy_training_action_training_resource_rel AS rel
    INNER JOIN academy_training_action_enrolment AS tae
        ON tae.training_action_id = rel.training_action_id
), activity_test AS (
    -- Tests in related activity
    SELECT
        tae."id" as enrolment_id,
        rel.training_resource_id
    FROM
        academy_training_activity_training_resource_rel AS rel
    INNER JOIN academy_training_action AS atc
        ON rel.training_activity_id = atc.training_activity_id
    INNER JOIN academy_training_action_enrolment AS tae
        ON tae.training_action_id = atc."id"

), all_tests AS (
    -- All tests, this list can contains duplicated ids
    SELECT
        enrolment_id,
        training_resource_id
    FROM
        action_test
    UNION ALL (
        SELECT
            enrolment_id,
            training_resource_id
        FROM
            activity_test
    )
    UNION ALL (
        SELECT
            enrolment_id,
            training_resource_id
        FROM
            module_test
    )
) SELECT DISTINCT
    enrolment_id,
    training_resource_id
FROM
    all_tests
"""
