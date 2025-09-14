# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from odoo.tools import drop_view_if_exists

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingActionAvailableResourceRel(models.Model):
    """ """

    _name = "academy.training.action.available.resource.rel"
    _description = "Academy training action available resource rel"

    _rec_name = "id"
    _order = "id ASC"

    _auto = False
    _table = "academy_training_action_available_resource_rel"
    _view_sql = """
        WITH module_resources AS (
            SELECT
                    atv."id" AS training_activity_id,
                    atr."id" AS training_resource_id
            FROM
                    academy_training_activity AS atv
            INNER JOIN academy_competency_unit AS acu
                    ON atv."id" = acu.training_activity_id
            INNER JOIN academy_training_module AS atm
                    ON acu.training_module_id = atm."id"
            LEFT JOIN academy_training_module AS atu
                    ON atm."id" = atu.training_module_id or atm."id" = atu."id"
            INNER JOIN academy_training_module_training_resource_rel AS rel
                    ON COALESCE (atu."id", atm."id") = rel.training_module_id
            LEFT JOIN academy_training_resource AS atr
                    ON rel.training_resource_id = atr."id"
        ), activity_resources AS (
            SELECT
                training_activity_id,
                training_resource_id
            FROM
                academy_training_activity_training_resource_rel AS rel
            UNION ALL (
                SELECT
                    training_activity_id,
                    training_resource_id
                FROM
                    module_resources
            )
        ), inherited_resources AS (
            SELECT
                atc."id" as training_action_id,
                ars.training_resource_id
            FROM
                activity_resources AS ars
            INNER JOIN academy_training_action atc
                ON ars.training_activity_id = atc.training_activity_id

        ) SELECT
            training_action_id,
            training_resource_id
        FROM
                academy_training_action_training_resource_rel AS rel
        UNION ALL (
            SELECT
                training_action_id,
                training_resource_id
            FROM
                inherited_resources
        )
    """

    training_action_id = fields.Many2one(
        string="Training action",
        required=True,
        readonly=False,
        index=False,
        default=None,
        help="Related training action",
        comodel_name="academy.training.action",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    training_resource_id = fields.Many2one(
        string="Training resource",
        required=True,
        readonly=False,
        index=False,
        default=None,
        help="Related training resource",
        comodel_name="academy.training.resource",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    def init(self):
        sentence = "CREATE or REPLACE VIEW {} as ( {} )"

        drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute(sentence.format(self._table, self._view_sql))

        self.prevent_actions()

    def prevent_actions(self):
        actions = ["INSERT", "UPDATE", "DELETE"]

        BASE_SQL = """
            CREATE OR REPLACE RULE {table}_{action} AS
                ON {action} TO {table} DO INSTEAD NOTHING
        """

        for action in actions:
            sql = BASE_SQL.format(table=self._table, action=action)
            self.env.cr.execute(sql)
