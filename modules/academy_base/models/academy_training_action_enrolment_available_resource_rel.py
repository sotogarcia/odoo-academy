# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from odoo.tools import drop_view_if_exists

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingActionEnrolmentAvailableResourceRel(models.Model):
    """
    """

    _name = 'academy.training.action.enrolment.available.resource.rel'
    _description = u'Academy training action enrolment available resource rel'

    _rec_name = 'id'
    _order = 'id ASC'

    _auto = False
    _table = 'academy_training_action_enrolment_available_resource_rel'
    _view_sql = '''
        WITH training_enrolments AS (

            SELECT DISTINCT
                rel.training_resource_id,
                tae."id" AS enrolment_id
            FROM
                academy_training_action_enrolment_training_resource_rel AS rel
            INNER JOIN academy_training_action_enrolment AS tae
                ON tae."id" = rel.enrolment_id

        ), training_actions AS (

            SELECT DISTINCT
                rel.training_resource_id,
                tae."id" AS enrolment_id
            FROM
                academy_training_action_training_resource_rel AS rel
            INNER JOIN academy_training_action AS ata
                ON ata."id" = rel."training_action_id"
            INNER JOIN academy_training_action_enrolment AS tae
                ON tae.training_action_id = ata."id"
            WHERE ata.active

        ), training_activities as (

            SELECT DISTINCT
                rel.training_resource_id,
                tae."id" AS enrolment_id
            FROM
                academy_training_activity_training_resource_rel AS rel
            INNER JOIN academy_training_activity AS atc
                ON atc."id" = rel.training_activity_id
            INNER JOIN academy_training_action AS ata
                ON ata.training_activity_id = atc."id"
            INNER JOIN academy_training_action_enrolment AS tae
                ON tae.training_action_id = ata."id"
            WHERE ata.active AND atc.active

        ), competency_units AS (

            SELECT DISTINCT
                rel.training_resource_id,
                tae."id" AS enrolment_id
            FROM
                academy_competency_unit_training_resource_rel AS rel
            INNER JOIN academy_competency_unit AS acu
                ON acu."id" = rel.competency_unit_id
            INNER JOIN academy_training_activity AS atc
                ON atc."id" = acu.training_activity_id
            INNER JOIN academy_training_action AS ata
                ON ata.training_activity_id = atc."id"
            INNER JOIN academy_training_action_enrolment AS tae
                ON tae.training_action_id = ata."id"
            WHERE ata.active AND atc.active AND acu.active

        ), training_modules AS (

            SELECT DISTINCT
                rel.training_resource_id,
                tae."id" AS enrolment_id
            FROM
                academy_training_module_training_resource_rel AS rel
            INNER JOIN academy_training_module_tree_readonly AS tree
                ON tree.requested_module_id = rel."training_module_id"
            INNER JOIN academy_training_module AS atm
                ON atm."id" = tree.responded_module_id
            INNER JOIN academy_competency_unit AS acu
                ON acu.training_module_id = atm."id"
            INNER JOIN academy_training_activity AS atc
                ON atc."id" = acu.training_activity_id
            INNER JOIN academy_training_action AS ata
                ON ata.training_activity_id = atc."id"
            INNER JOIN academy_training_action_enrolment AS tae
                ON tae.training_action_id = ata."id"
            WHERE ata.active AND atc.active AND acu.active AND atm.active

        )
        SELECT enrolment_id, training_resource_id
            FROM training_enrolments UNION ALL
        SELECT enrolment_id, training_resource_id
            FROM training_actions UNION ALL
        SELECT enrolment_id, training_resource_id
            FROM training_activities UNION ALL
        SELECT enrolment_id, training_resource_id
            FROM competency_units UNION ALL
        SELECT enrolment_id, training_resource_id
            FROM training_modules
    '''

    enrolment_id = fields.Many2one(
        string='Enrolment',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Related training action enrolment',
        comodel_name='academy.training.action.enrolment',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    training_resource_id = fields.Many2one(
        string='Training resource',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Related training resource',
        comodel_name='academy.training.resource',
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
