# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from odoo.tools import drop_view_if_exists

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTestsTestTrainingAssignmentStudentRel(models.Model):
    """ This act as middle relation in many to many relationship between
    academy.tests.test.training.assignment and academy.student
    """

    _name = 'academy.tests.test.training.assignment.student.rel'
    _description = u'Academy tests test training assignment student'

    _order = 'assignment_id DESC, student_id DESC'

    _auto = False

    assignment_id = fields.Many2one(
        string='Assignment',
        required=True,
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
        string='Student',
        required=True,
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

    # Raw sentence used to create new model based on SQL VIEW
    _view_sql = '''
        WITH training_enrolments AS (
            SELECT DISTINCT
                tta.id AS assignment_id,
                tta.training_ref,
                tae.student_id
            FROM academy_tests_test_training_assignment tta
            JOIN academy_training_action_enrolment tae
                ON tae.id = tta.enrolment_id
        ), training_actions AS (
            SELECT
                DISTINCT tta.id AS assignment_id,
                tta.training_ref,
                tae.student_id
            FROM academy_tests_test_training_assignment tta
            JOIN academy_training_action ata
                ON ata.id = tta.training_action_id
            JOIN academy_training_action_enrolment tae
                ON tae.training_action_id = ata.id
            WHERE
                ata.active
        ), training_activities AS (
            SELECT DISTINCT
                tta.id AS assignment_id,
                tta.training_ref,
                tae.student_id
            FROM academy_tests_test_training_assignment tta
            JOIN academy_training_activity atc
                ON atc.id = tta.training_activity_id
            JOIN academy_training_action ata
                ON ata.training_activity_id = atc.id
            JOIN academy_training_action_enrolment tae
                ON tae.training_action_id = ata.id
            WHERE
                ata.active AND
                atc.active
        ), competency_units AS (
            SELECT DISTINCT
                tta.id AS assignment_id,
                tta.training_ref,
                tae.student_id
            FROM academy_tests_test_training_assignment tta
            JOIN academy_competency_unit acu
                ON acu.id = tta.competency_unit_id
            JOIN academy_training_activity atc
                ON atc.id = acu.training_activity_id
            JOIN academy_training_action ata
                ON ata.training_activity_id = atc.id
            JOIN academy_training_action_enrolment tae
                ON tae.training_action_id = ata.id
            WHERE
                ata.active AND
                atc.active AND
                acu.active
        ), training_modules AS (
            SELECT DISTINCT
                tta.id AS assignment_id,
                tta.training_ref,
                tae.student_id
            FROM academy_tests_test_training_assignment tta
            JOIN academy_training_module_rel tree
                ON tree.requested_module_id = tta.training_module_id
            JOIN academy_training_module atm
                ON atm.id = tree.responded_module_id
            JOIN academy_competency_unit acu
                ON acu.training_module_id = atm.id
            JOIN academy_training_activity atc
                ON atc.id = acu.training_activity_id
            JOIN academy_training_action ata
                ON ata.training_activity_id = atc.id
            JOIN academy_training_action_enrolment tae
                ON tae.training_action_id = ata.id
            WHERE
                ata.active AND
                atc.active AND
                acu.active AND
                atm.active
        )
        SELECT
            training_enrolments.assignment_id,
            training_enrolments.student_id
        FROM training_enrolments
        UNION ALL
        SELECT
            training_actions.assignment_id,
            training_actions.student_id
        FROM training_actions
        UNION ALL
        SELECT
            training_activities.assignment_id,
            training_activities.student_id
        FROM training_activities
        UNION ALL
        SELECT
            competency_units.assignment_id,
            competency_units.student_id
        FROM competency_units
        UNION ALL
        SELECT
            training_modules.assignment_id,
            training_modules.student_id
        FROM training_modules
'''
