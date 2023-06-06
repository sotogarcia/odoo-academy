# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from odoo.tools import drop_view_if_exists

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingModuleUsedInTrainingActionRel(models.Model):
    """
    """

    _name = 'academy.training.module.used.in.training.action.rel'
    _description = u'Academy training module used in training action rel'

    _rec_name = 'id'
    _order = 'id ASC'

    _auto = False
    _table = 'academy_training_module_used_in_training_action_rel'
    _view_sql = '''
        SELECT
            atm."id" AS training_module_id,
            ata."id" AS training_action_id
        FROM
            academy_training_module AS atm
        INNER JOIN academy_competency_unit AS acu
            ON acu.training_module_id = atm."id"
        INNER JOIN academy_training_activity AS atc
            ON atc."id" = acu.training_activity_id
        INNER JOIN academy_training_action AS ata
            ON ata.training_activity_id = atc."id"
    '''

    training_module_id = fields.Many2one(
        string='Training module',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Related training module',
        comodel_name='academy.training.module',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    training_action_id = fields.Many2one(
        string='Training action',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Related training action',
        comodel_name='academy.training.action',
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
