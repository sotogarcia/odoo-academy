# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from logging import getLogger
from odoo.tools import drop_view_if_exists


_logger = getLogger(__name__)


class AcademyTestsTestTrainingAssignmentStudentRel(models.Model):
    """ SQL VIEW will be used as middle many to many relationship
    """

    _name = 'academy.tests.test.training.assignment.student.rel'
    _description = u'Academy tests test training assignment student rel'

    _auto = False
    _table = 'academy_tests_test_training_assignment_student_rel'
    _view_sql = '''
    WITH training_enrolments AS (

        SELECT DISTINCT
            tta."id" AS assignment_id,
            tta.training_ref,
            tae.student_id
        FROM
            academy_tests_test_training_assignment AS tta
        INNER JOIN academy_training_action_enrolment AS tae
            ON tae."id" = tta.enrolment_id

    ), training_actions AS (

        SELECT DISTINCT
            tta."id" AS assignment_id,
            tta.training_ref,
            tae.student_id
        FROM
            academy_tests_test_training_assignment AS tta
        INNER JOIN academy_training_action AS ata
            ON ata."id" = tta."training_action_id"
        INNER JOIN academy_training_action_enrolment AS tae
            ON tae.training_action_id = ata."id"
        WHERE ata.active

    ), training_activities as (

        SELECT DISTINCT
            tta."id" AS assignment_id,
            tta.training_ref,
            tae.student_id
        FROM
            academy_tests_test_training_assignment AS tta
        INNER JOIN academy_training_activity AS atc
            ON atc."id" = tta.training_activity_id
        INNER JOIN academy_training_action AS ata
            ON ata.training_activity_id = atc."id"
        INNER JOIN academy_training_action_enrolment AS tae
            ON tae.training_action_id = ata."id"
        WHERE ata.active AND atc.active

    ), competency_units AS (

        SELECT DISTINCT
            tta."id" AS assignment_id,
            tta.training_ref,
            tae.student_id
        FROM
            academy_tests_test_training_assignment AS tta
        INNER JOIN academy_competency_unit AS acu
            ON acu."id" = tta.competency_unit_id
        INNER JOIN academy_training_activity AS atc
            ON atc."id" = acu.training_activity_id
        INNER JOIN academy_training_action AS ata
            ON ata.training_activity_id = atc."id"
        INNER JOIN academy_training_action_enrolment AS tae
            ON tae.training_action_id = ata."id"
        WHERE ata.active AND atc.active AND acu.active

    ), training_modules AS (

        SELECT DISTINCT
            tta."id" AS assignment_id,
            tta.training_ref,
            tae.student_id
        FROM
            academy_tests_test_training_assignment AS tta
        INNER JOIN academy_training_module_tree_readonly AS tree
            ON tree.requested_module_id = tta."training_module_id"
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
    SELECT assignment_id, student_id FROM training_enrolments UNION ALL
    SELECT assignment_id, student_id FROM training_actions UNION ALL
    SELECT assignment_id, student_id FROM training_activities UNION ALL
    SELECT assignment_id, student_id FROM competency_units UNION ALL
    SELECT assignment_id, student_id FROM training_modules
    '''

    assignment_id = fields.Many2one(
        string='Assignment',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Related assignment',
        comodel_name='academy.tests.test.training.assignment',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    student_id = fields.Many2one(
        string='Tests block',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Related student',
        comodel_name='academy.student',
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
