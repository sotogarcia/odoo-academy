# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from odoo.tools import drop_view_if_exists

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingActionStudentRel(models.Model):
    """
    """

    _name = 'academy.training.action.student.rel'
    _description = u'Academy training action student rel'

    _rec_name = 'id'
    _order = 'id ASC'

    _auto = False
    _table = 'academy_training_action_student_rel'
    _check_company_auto = True

    _view_sql = '''
        SELECT
            student_id,
            training_action_id,
            enrol.company_id
        FROM
            academy_training_action_enrolment AS enrol
        INNER JOIN academy_training_action AS ata
            ON ata."id" = enrol.training_action_id
        WHERE
            register <= CURRENT_TIMESTAMP ( 0 )
            AND ( deregister > CURRENT_TIMESTAMP ( 0 ) OR deregister IS NULL )
            AND enrol.active
    '''
    company_id = fields.Many2one(
        string='Company',
        required=True,
        readonly=True,
        index=True,
        default=lambda self: self.env.company,
        help='The company this record belongs to',
        comodel_name='res.company',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    student_id = fields.Many2one(
        string='Student',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Related student',
        comodel_name='academy.student',
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
