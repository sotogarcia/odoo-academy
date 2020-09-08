# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger
from odoo.tools import drop_view_if_exists

_logger = getLogger(__name__)


SQL_FOR_ACADEMY_RANDOM_TEMPLATE_SCHEDULED_REL = '''
WITH from_activity AS (
    SELECT
        rel.random_template_id,
        tae."id" AS enrolment_id,
        \'academy.training.action\'::VARCHAR AS model,
        ata."id" as res_id,
        tae.student_id,
        \'academy.training.action\'::VARCHAR || ',' ||ata."id" as record,
        (trt.active AND ata.active AND tae.active)::BOOLEAN as active
    FROM
        academy_training_action_enrolment AS tae
    INNER JOIN academy_training_action AS ata
        ON ata."id" = tae.training_action_id
    INNER JOIN academy_training_activity AS atc
        ON atc."id" = ata.training_activity_id
    INNER JOIN academy_tests_random_template_training_activity_rel AS rel
        ON rel.training_activity_id = atc."id"
    INNER JOIN academy_tests_random_template AS trt
        ON trt."id" = rel.random_template_id
), from_module AS (
    SELECT
        rel2.random_template_id,
        tae."id" AS enrolment_id,
        \'academy.training.module\'::VARCHAR AS model,
        rel1.training_module_id AS res_id,
        tae.student_id,
        \'academy.training.module\'::VARCHAR || \',\' || rel1.training_module_id AS record,
        (trt.active AND atm.active AND tae.active)::BOOLEAN as active
    FROM
        academy_training_action_enrolment AS tae
    INNER JOIN academy_action_enrolment_training_module_rel AS rel1
        ON tae."id" = rel1.action_enrolment_id
    INNER JOIN academy_tests_random_template_training_module_rel AS rel2
        ON rel1.training_module_id = rel2.training_module_id
    INNER JOIN academy_training_module AS atm
        ON atm."id" = rel1.training_module_id
    INNER JOIN academy_tests_random_template AS trt
        ON trt."id" = rel2.random_template_id
), from_all AS (
    (SELECT
        *
    FROM
        from_activity) UNION (
    SELECT
        *
    FROM
    from_module)
) SELECT
    ROW_NUMBER() OVER() AS "id",
    trt.create_uid,
    trt.create_date,
    trt.write_uid,
    trt.write_date,
    fa.active,
    random_template_id,
    enrolment_id,
    student_id,
    model,
    res_id,
    record
FROM from_all AS fa
INNER JOIN academy_tests_random_template AS trt
    ON trt."id" = fa.random_template_id
WHERE trt.allow_automate = True
'''


class AcademyRandomTemplateScheduledWizard(models.Model):
    """ The summary line for a class docstring should fit on one line.

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.random.template.scheduled.rel'
    _description = u'Template scheduled relationship'

    _rec_name = 'id'
    _order = 'id ASC'

    _table='academy_random_template_scheduled_rel'

    _auto = False

    enrolment_id = fields.Many2one(
        string='Enrolment',
        required=True,
        readonly=True,
        index=False,
        default=None,
        help='Choose enrolment',
        comodel_name='academy.training.action.enrolment',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    random_template_id = fields.Many2one(
        string='Random template',
        required=True,
        readonly=True,
        index=False,
        default=None,
        help='Choose random template for test',
        comodel_name='academy.tests.random.template',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    model = fields.Selection(
        string='Resource',
        required=True,
        readonly=True,
        index=False,
        default='Choose the type of resource',
        help=False,
        selection=[
            ('academy.training.activity', 'Activity'),
            ('academy.training.module', 'Module')
        ]
    )

    res_id = fields.Integer(
        string='Resource ID',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help='Choose resource identifier'
    )

    student_id = fields.Many2one(
        string='Student',
        required=True,
        readonly=True,
        index=False,
        default=None,
        help='Choose student',
        comodel_name='academy.student',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    record = fields.Reference(
        string='Resource record',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help=False,
        selection=[
            ('academy.training.action', 'Action'),
            ('academy.training.module', 'Module')
        ]
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
        drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute('''CREATE or REPLACE VIEW {} as (
            {}
        )'''.format(
            self._table,
            SQL_FOR_ACADEMY_RANDOM_TEMPLATE_SCHEDULED_REL)
        )

        self.prevent_actions()
