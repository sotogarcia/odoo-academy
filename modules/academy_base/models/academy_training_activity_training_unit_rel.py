# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from odoo.tools import drop_view_if_exists

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingActivityTrainingUnitRel(models.Model):
    """
    """

    _name = 'academy_training_activity_training_unit_rel'
    _description = u'Academy training activity training unit rel'

    _rec_name = 'id'
    _order = 'id ASC'

    _auto = False
    _table = 'academy_training_activity_training_unit_rel'
    _view_sql = '''
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
    '''

    training_activity_id = fields.Many2one(
        string='Training activity',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Related training activity',
        comodel_name='academy.training.activity',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    training_unit_id = fields.Many2one(
        string='Training unit',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Related training unit',
        comodel_name='academy.training.module',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    def init(self):
        sentence = 'CREATE or REPLACE VIEW {} as ( {} )'

        drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute(sentence.format(self._table, self._view_sql))

        self.prevent_actions()

    def prevent_actions(self):
        actions = ['INSERT', 'UPDATE', 'DELETE']

        BASE_SQL = '''
            CREATE OR REPLACE RULE {table}_{action} AS
                ON {action} TO {table} DO INSTEAD NOTHING
        '''

        for action in actions:
            sql = BASE_SQL.format(table=self._table, action=action)
            self.env.cr.execute(sql)
