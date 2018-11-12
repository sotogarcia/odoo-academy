# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from openerp.fields import Many2many, Default
from openerp.tools import sql as sqltools
from logging import getLogger


_logger = getLogger(__name__)


class Many2ManyThroughView(Many2many):
    """ Custom Many2many field, it uses a SQL view as middle """


    def __init__(self, comodel_name=Default, relation=Default, column1=Default,
                 column2=Default, string=Default, statement=Default, **kwargs):
        """ Constructor overload, it ensures parent constructor will be called
        """

        super(Many2ManyThroughView, self).__init__(
            comodel_name=comodel_name,
            relation=relation,
            column1=column1,
            column2=column2,
            string=string,
            **kwargs
        )

    def update_db(self, model, columns):
        """ Overload method to create middle relation. This will make 
        a new SQL VIEW instead a SQL TABLE.
        """

        # Parent method will never been called
        # super(Many2ManyThroughView, self).update_db(model, columns) 

        if self._view_can_be_built(model) and \
           self._view_needs_update(model.env.cr):

            self._notify_the_update() # in log
            self._drop_relation_if_exists(model.env.cr)
            self._create_view(model.env.cr)


    # ------------------------- AUXILIARY METHODS -----------------------------


    def _notify_the_update(self):
        """ Write log message telling SQL VIEW will be created 
        instead a TABLE. This message will be shown before the
        proccess starts announcing what is going to be done.
        """

        msg = 'Creating SQL VIEW {} as middle table for {} field'
        _logger.debug(msg.format(self.relation, self.name))


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
            return False
        
        # If some of the arguments has default value
        elif self.relation == Default or self.column1 == Default or \
           self.column2 == Default:
            return False

        # Relation has a related SQL statement
        elif not getattr(self, self.relation.upper()):
            return False

        # Left table and right table must exist before VIEW creation
        elif not self._both_tables_already_exist(model):
            return False

        else:
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

        sql='''
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
        
        return result and result[0] == True


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
            sqltools.drop_view_if_exists(cursor, self.relation)


    def _create_view(self, cursor):
        """ It gets VIEW select statement from class constant and 
        fills the col1 and col2 string arguments in SQL statement whith
        the names of the columns supplied in field definition. 
        
        Secondly, builds SQL statement to create VIEW using relation
        name and previously filled SQL select statement.

        Finally it executes SQL command to create the middle view.
        """

        select_sql = getattr(self, self.relation.upper())
        select_sql = select_sql.format(col1=self.column1, col2=self.column2)

        create_sql = 'CREATE VIEW {} AS {};'.format(
            self.relation, select_sql)
        
        cursor.execute(create_sql)


    # ----------- SQL STATEMENTS WILL BE USED IN VIEW DEFINITIONS -------------S


    ACADEMY_TRAINING_ACTION_ACADEMY_TRAINING_RESOURCE_REL = '''
        SELECT
            ata."id" AS academy_training_action_id,
            atr."id" AS academy_training_resource_id
        FROM
            academy_training_resource AS atr
        INNER JOIN academy_training_resource_academy_training_unit_rel AS rel ON rel.academy_training_resource_id = atr."id"
        INNER JOIN academy_training_unit AS atu ON rel.academy_training_unit_id = atu."id"
        INNER JOIN academy_training_module AS atm ON atm."id" = atu.academy_training_module_id
        INNER JOIN academy_competency_unit AS acu ON acu.academy_training_module_id = atm."id"
        INNER JOIN academy_professional_qualification AS apc ON acu.professional_qualification_id = apc."id"
        INNER JOIN academy_training_action AS ata ON ata.professional_qualification_id = apc."id"
    '''