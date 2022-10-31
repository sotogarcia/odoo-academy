# -*- coding: utf-8 -*-
""" AcademyTrainingModuleTreeReadonly

This module contains the academy.training.module.rel Odoo model which
allows to quick search module dependencies.
"""

from odoo import models, fields
from odoo.tools import drop_view_if_exists

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingModuleRel(models.Model):
    """ Training modules may be composed of several training units, this model
    uses a SQL view to relate a module to all its units
    """

    _name = 'academy.training.module.rel'
    _description = u'Academy training module tree readonly'

    _rec_name = 'requested_module_id'
    _order = 'requested_module_id ASC,  responded_module_id ASC'
    _auto = False

    requested_module_id = fields.Many2one(
        string='Requested',
        required=True,
        readonly=True,
        index=False,
        default=None,
        help='Module will be searched',
        comodel_name='academy.training.module',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    parent_module_id = fields.Many2one(
        string='Parent',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Parent module for the searched one',
        comodel_name='academy.training.module',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    responded_module_id = fields.Many2one(
        string='Responded',
        required=True,
        readonly=True,
        index=False,
        default=None,
        help='This can be the module itself or its units',
        comodel_name='academy.training.module',
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
        WITH own_id AS (

            -- Request modules by id and respond with the own id
            SELECT
                "create_uid",
                "create_date",
                "write_uid",
                "write_date",
                "id" AS requested_module_id,
                "id" AS responded_module_id,
                "training_module_id" AS parent_module_id
            FROM
                academy_training_module

        ),  parent_id AS (

            -- Request modules by own id and respond with the parent id
            SELECT
                "create_uid",
                "create_date",
                "write_uid",
                "write_date",
                "id" AS requested_module_id,
                "training_module_id" AS responded_module_id,
                null::INTEGER AS parent_module_id
            FROM
                academy_training_module
            WHERE
                training_module_id IS NOT NULL

        ), child_id AS (

            -- Request modules by parent id and respond with own id
            SELECT
                "create_uid",
                "create_date",
                "write_uid",
                "write_date",
                "training_module_id" AS requested_module_id,
                "id" AS responded_module_id,
                training_module_id AS parent_module_id
            FROM
                academy_training_module
            WHERE
                training_module_id IS NOT NULL

        ), full_set as (

            -- Merge all queries into a single recordset
            SELECT
            *
            FROM
                own_id
            UNION ALL SELECT
                *
            FROM
                parent_id
            UNION ALL SELECT
                *
            FROM
                child_id

        ) SELECT
            "create_uid",
            "create_date",
            "write_uid",
            "write_date",
            requested_module_id,
            responded_module_id,
            parent_module_id
        FROM
            full_set
        ORDER BY
            requested_module_id ASC,
            responded_module_id ASC
    '''
