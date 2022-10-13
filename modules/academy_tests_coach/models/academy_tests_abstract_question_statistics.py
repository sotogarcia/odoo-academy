# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from odoo.tools import drop_view_if_exists

from .utils.view_academy_tests_question_statistics_helper import \
    VIEW_ACADEMY_TESTS_QUESTION_STATISTICS_HELPER

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTestabstractQuestionStatistics(models.AbstractModel):

    _name = 'academy.tests.abstract.question.statistics'
    _description = u'Academy tests question statistics'

    _rec_name = 'id'
    _order = 'id DESC'

    _auto = True

    _groupby = None
    _related = None

    question_id = fields.Many2one(
        string='Question',
        required=True,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.question',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    first_time = fields.Datetime(
        string='First time',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False
    )

    last_time = fields.Datetime(
        string='Last time',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False
    )

    retries = fields.Integer(
        string='Retries',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help=False
    )

    blank_count = fields.Integer(
        string='Blank count',
        required=False,
        readonly=False,
        index=False,
        default=0,
        help=False
    )

    answer_count = fields.Integer(
        string='Answer count',
        required=False,
        readonly=False,
        index=False,
        default=0,
        help=False
    )

    doubt_count = fields.Integer(
        string='Doubt count',
        required=False,
        readonly=False,
        index=False,
        default=0,
        help=False
    )

    right_count = fields.Integer(
        string='Right count',
        required=False,
        readonly=False,
        index=False,
        default=0,
        help=False
    )

    wrong_count = fields.Integer(
        string='Wrong count',
        required=False,
        readonly=False,
        index=False,
        default=0,
        help=False
    )

    answer_doubt_count = fields.Integer(
        string='Answer/doubt count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help=False
    )

    wrong_blank_count = fields.Integer(
        string='Wrong/blank count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help=False
    )

    wrong_doubt_count = fields.Integer(
        string='Wrong/doubt count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help=False
    )

    wrong_blank_doubt_count = fields.Integer(
        string='Wrong/blank/doubt count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help=False
    )

    blank_percent = fields.Float(
        string='Blank percent',
        required=False,
        readonly=False,
        index=False,
        default=0.0,
        digits=(16, 2),
        help=False
    )

    answer_percent = fields.Float(
        string='Answer percent',
        required=False,
        readonly=False,
        index=False,
        default=0.0,
        digits=(16, 2),
        help=False
    )

    doubt_percent = fields.Float(
        string='Doubt percent',
        required=False,
        readonly=False,
        index=False,
        default=0.0,
        digits=(16, 2),
        help=False
    )

    right_percent = fields.Float(
        string='Right percent',
        required=False,
        readonly=False,
        index=False,
        default=0.0,
        digits=(16, 2),
        help=False
    )

    wrong_percent = fields.Float(
        string='Wrong percent',
        required=False,
        readonly=False,
        index=False,
        default=0.0,
        digits=(16, 2),
        help=False
    )

    answer_doubt_percent = fields.Float(
        string='Answer/doubt percent',
        required=False,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help=False
    )

    wrong_blank_percent = fields.Float(
        string='Wrong/blank percent',
        required=False,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help=False
    )

    wrong_doubt_percent = fields.Float(
        string='Wrong/doubt percent',
        required=False,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help=False
    )

    wrong_blank_doubt_percent = fields.Float(
        string='Wrong/blank/doubt percent',
        required=False,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help=False
    )

    def _build_view_sql(self):
        """ This SQL view requires as part of its code the previously used in
        another SQL view

        Returns:
            str: full SQL query will be used in SQL view
        """

        final_obj = self.env['academy.tests.attempt.final.answer.helper']
        final_sql = final_obj.build_view_sql()

        enrolment_obj = self.env['academy.training.action.enrolment']
        available_sql = enrolment_obj.sql_available_assignment_ids()

        main = VIEW_ACADEMY_TESTS_QUESTION_STATISTICS_HELPER

        return main.format(
            final=final_sql,
            available=available_sql,
            groupby=self._groupby,
            related=self._related
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
        if not self._auto:
            pattern = '''CREATE or REPLACE VIEW {} as ({})'''
            sentence = pattern.format(self._table, self._build_view_sql())

            drop_view_if_exists(self.env.cr, self._table)

            self.env.cr.execute(sentence)

            self.prevent_actions()
