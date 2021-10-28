# -*- coding: utf-8 -*-
""" AcademyTestsQuestion

This module contains the academy.tests.question.changelog.entry Odoo model
which uses an SQL view to get all question tracking messages.
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools import drop_view_if_exists
from logging import getLogger


_logger = getLogger(__name__)


ACADEMY_TESTS_QUESTION_CHANGELOG_ENTRY = '''
    WITH valid_subtypes AS (
        SELECT
            res_id
        FROM
            ir_model_data
        WHERE
            model = 'mail.message.subtype'
        AND "module" = 'academy_tests'
        AND "name" IN (
            'academy_tests_question_written',
            'academy_tests_test_written',
            'academy_tests_answer_written'
        )

    )
    SELECT
        ROW_NUMBER() OVER(ORDER BY mm.res_id ASC, mm.write_date DESC) AS "id",
        mm."id" AS message_id,
        mtv."id" AS tracking_id,
        mm.res_id AS question_id,
        mm.create_uid,
        mm.create_date,
        mm.write_uid,
        mm.write_date
    FROM
        mail_message AS mm
    INNER JOIN mail_tracking_value AS mtv
        ON mm."id" = mtv.mail_message_id
    INNER JOIN valid_subtypes AS vs
        ON vs.res_id = mm.subtype_id
    WHERE
        model = 'academy.tests.question'
    AND mtv.field IN ('name', 'preamble', 'is_correct')
'''


class AcademyTestsQuestionChangelogEntry(models.Model):
    """
    """

    _name = 'academy.tests.question.changelog.entry'
    _description = u'Academy tests question changelog entry'

    _rec_name = 'id'
    _order = 'write_date desc, question_id ASC'

    _auto = False

    _view_sql = ACADEMY_TESTS_QUESTION_CHANGELOG_ENTRY

    create_date = fields.Datetime(
        string='Created on',
        required=False,
        readonly=True,
        index=False,
        help=False
    )

    write_date = fields.Datetime(
        string='Last updated on',
        required=False,
        readonly=True,
        index=False,
        help=False
    )

    create_uid = fields.Many2one(
        string='Created by',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='res.users',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    write_uid = fields.Many2one(
        string='Last Updated by',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='res.users',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

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

    message_id = fields.Many2one(
        string='Message',
        required=True,
        readonly=True,
        index=False,
        default=None,
        help='Show related mail message',
        comodel_name='mail.message',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    tracking_id = fields.Many2one(
        string='Tracking',
        required=True,
        readonly=True,
        index=False,
        default=None,
        help='Show related mail tracking value',
        comodel_name='mail.tracking.value',
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
