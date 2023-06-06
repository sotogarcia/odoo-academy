# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from logging import getLogger
from odoo.tools import drop_view_if_exists


_logger = getLogger(__name__)


ACADEMY_TRAINING_AVAILABLE_ITEMS_REL = '''
    WITH enrolments AS (
        SELECT
            tae."id" AS enrolment_id,
            ass."id" AS related_id
        FROM
            academy_training_action_enrolment AS tae
            INNER JOIN academy_action_enrolment_competency_unit_rel AS rel
                ON rel.action_enrolment_id = tae."id"
            INNER JOIN {related} AS ass
                ON ass.enrolment_id = tae."id" AND (
                    ass.secondary_id IS NULL OR
                    ass.secondary_id = rel.competency_unit_id
                )
    ), actions AS(
        SELECT
            tae."id" AS enrolment_id,
            ass."id" AS related_id
        FROM
            academy_training_action_enrolment AS tae
            INNER JOIN academy_action_enrolment_competency_unit_rel AS rel
                ON rel.action_enrolment_id = tae."id"
            INNER JOIN academy_training_action AS ata
                ON ata."id" = tae.training_action_id
            INNER JOIN {related} AS ass
                ON ass.training_action_id = ata."id" AND (
                    ass.secondary_id IS NULL OR
                    ass.secondary_id = rel.competency_unit_id
                )
            WHERE ata.active IS TRUE
    ), activities AS (
        SELECT
            tae."id" AS enrolment_id,
            ass."id" AS related_id
        FROM
            academy_training_action_enrolment AS tae
            INNER JOIN academy_action_enrolment_competency_unit_rel AS rel
                ON rel.action_enrolment_id = tae."id"
            INNER JOIN academy_training_action AS ata
                ON ata."id" = tae.training_action_id
            inner join academy_training_activity AS atc
                ON atc."id" = ata.training_activity_id
            INNER JOIN {related} AS ass
                ON ass.training_activity_id = atc."id" AND (
                    ass.secondary_id IS NULL OR
                    ass.secondary_id = rel.competency_unit_id
                )
            WHERE ata.active IS TRUE AND atc.active IS TRUE
    )
    , competencies AS (
        SELECT
            tae."id" AS enrolment_id,
            ass."id" AS related_id
        FROM
            academy_training_action_enrolment AS tae
            INNER JOIN academy_action_enrolment_competency_unit_rel AS rel
                ON rel.action_enrolment_id = tae."id"
            INNER JOIN academy_competency_unit AS acu
                ON acu."id" = rel.competency_unit_id
            INNER JOIN {related} AS ass
                ON ass.competency_unit_id = acu."id"
            WHERE acu.active IS TRUE
    ), modules AS (
      SELECT
            tae."id" AS enrolment_id,
            ass."id" AS related_id
        FROM
            academy_training_action_enrolment AS tae
            INNER JOIN academy_action_enrolment_competency_unit_rel AS rel
                ON rel.action_enrolment_id = tae."id"
            INNER JOIN academy_competency_unit AS acu
                ON acu."id" = rel.competency_unit_id
            INNER JOIN academy_training_module_tree_readonly AS tree
                ON tree.requested_module_id = acu.training_module_id
            INNER JOIN academy_training_module AS atm
                ON atm."id" = tree.responded_module_id
            INNER JOIN {related} AS ass
                ON ass."training_module_id" = atm."id"
            WHERE acu.active IS TRUE AND atm.active IS TRUE
    ), training AS (
        SELECT * FROM enrolments UNION DISTINCT
        SELECT * FROM actions UNION DISTINCT
        SELECT * FROM activities UNION DISTINCT
        SELECT * FROM competencies UNION DISTINCT
        SELECT * FROM modules
    ) SELECT * FROM training
'''


class AcademyTrainingActionEnrolmentAvailableAssignmentRel(models.Model):
    """ SQL VIEW will be used as middle many to many relationship
    """

    _name = 'academy.training.action.enrolment.available.assignment.rel'
    _description = 'Academy training action enrolment available assignment rel'

    _auto = False
    _table = 'academy_training_action_enrolment_available_assignment_rel'

    question_id = fields.Many2one(
        string='Question',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Original question',
        comodel_name='academy.tests.question',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    duplicate_id = fields.Many2one(
        string='Duplicated',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Duplicated question',
        comodel_name='academy.tests.question',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    def _sql_available_assignment_ids(self):
        query = ACADEMY_TRAINING_AVAILABLE_ITEMS_REL

        related = 'academy_tests_test_training_assignment'

        return query.format(related=related)

    def init(self):
        sentence = 'CREATE or REPLACE VIEW {} as ( {} )'

        drop_view_if_exists(self.env.cr, self._table)

        view_sql = self._sql_available_assignment_ids()
        self.env.cr.execute(sentence.format(self._table, view_sql))

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
