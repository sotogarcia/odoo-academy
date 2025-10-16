# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


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
    """This act as middle relation in many to many relationship between
    academy.training.action and academy.student
    """

    _name = "academy.training.action.student.rel"
    _description = "Academy training action student"

    _order = "training_action_id DESC, field_name DESC"
    _table = "academy_training_action_student_rel"

    _auto = False

    training_action_id = fields.Many2one(
        string="Training action",
        required=True,
        readonly=True,
        index=True,
        default=None,
        help="Related training action",
        comodel_name="academy.training.action",
        domain=[],
        context={},
        ondelete="restrict",
        auto_join=False,
    )

    student_id = fields.Many2one(
        string="Student",
        required=True,
        readonly=True,
        index=True,
        default=None,
        help="Related student",
        comodel_name="academy.student",
        domain=[],
        context={},
        ondelete="restrict",
        auto_join=False,
    )

    def prevent_actions(self):
        actions = ["INSERT", "UPDATE", "DELETE"]

        BASE_SQL = """
            CREATE OR REPLACE RULE {table}_{action} AS
                ON {action} TO {table} DO INSTEAD NOTHING
        """

        for action in actions:
            sql = BASE_SQL.format(table=self._table, action=action)
            self.env.cr.execute(sql)

    def init(self):
        sentence = """CREATE or REPLACE VIEW {} as ({})"""

        drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute(sentence.format(self._table, self._view_sql))

        self.prevent_actions()

    # Raw sentence used to create new model based on SQL VIEW
    _view_sql = """
        WITH enrolment_source AS (
          SELECT
            training_action_id,
            parent_action_id,
            student_id
          FROM
            academy_training_action_enrolment
          WHERE
            "active"
            -- AND register <= CURRENT_TIMESTAMP AT TIME ZONE 'UTC'
            -- AND (
            --     deregister IS NULL
            --     OR deregister > CURRENT_TIMESTAMP AT TIME ZONE 'UTC'
            -- )
        )
        SELECT
            training_action_id,
            student_id
        FROM enrolment_source
        UNION
        SELECT
            parent_action_id AS training_action_id,
            student_id
        FROM enrolment_source
    """
