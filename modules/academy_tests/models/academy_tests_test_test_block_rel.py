# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from odoo.tools import drop_view_if_exists

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTestsTestTestBlockRel(models.Model):
    """ This act as middle relation in many to many relationship
    """

    _name = 'academy.tests.test.test.block.rel'
    _description = u'List blocks by test'

    _order = 'test_id DESC,  test_block_id DESC'

    _auto = False


    test_id = fields.Many2one(
        string='Question',
        required=True,
        readonly=True,
        index=True,
        default=None,
        help='Related test',
        comodel_name='academy.tests.test',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    test_block_id = fields.Many2one(
        string='Test block',
        required=True,
        readonly=True,
        index=True,
        default=None,
        help='Related test block',
        comodel_name='academy.tests.test.block',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    def prevent_actions(self):
        actions = ['INSERT', 'UPDATE', 'DELETE']

        BASE_SQL = '''
            CREATE OR REPLACE RULE {table}_{action} AS
                ON {action} TO {table} DO INSTEAD NOTHING
        '''

        for action in actions:
            sql = BASE_SQL.format(table=self._table, action=action)
            self.env.cr.execute(sql)

    def init(self):
        sentence = '''CREATE or REPLACE VIEW {} as ({})'''

        drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute(sentence.format(self._table, self._view_sql))

        self.prevent_actions()

    _view_sql = '''
        SELECT DISTINCT
            test_id,
            test_block_id
        FROM
            academy_tests_test_question_rel
        WHERE
            test_block_id IS NOT NULL
    '''
