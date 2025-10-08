# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.osv.expression import TRUE_DOMAIN
from odoo.addons.academy_base.utils.sql_helpers import create_index

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingActionFacilityLink(models.Model):
    """ """

    _name = "academy.training.action.facility.link"
    _description = "Academy training action facility link"

    _inherits = {"facility.facility": "facility_id"}

    training_action_id = fields.Many2one(
        string="Training action",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Related training action",
        comodel_name="academy.training.action",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    action_line_id = fields.Many2one(
        string="Program unit",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Related training action",
        comodel_name="academy.training.action.line",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    facility_id = fields.Many2one(
        string="Facility",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Related educational facility",
        comodel_name="facility.facility",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    sequence = fields.Integer(
        string="Sequence",
        required=True,
        readonly=False,
        index=True,
        default=0,
        help="Educational facility priority order",
    )

    # -- Constraints ----------------------------------------------------------

    _sql_constraints = [
        (
            "unique_training_action_facility",
            "UNIQUE(training_action_id, facility_id)",
            "Facility already has been set to this training action",
        )
    ]

    # -- Methods overrides ----------------------------------------------------

    def init(self):
        """
        Ensure a supporting composite index exists for the
        primary-facility compute (ORDER BY training_action_id, sequence, id).
        """
        # Composite index fields, in the same order used by the query
        fields = ["training_action_id", "sequence", "id"]

        # Use a short, deterministic name to stay under PostgreSQL's 63-char limit
        index_name = f"{self._table}__primary_facility_idx"

        create_index(
            self.env,
            self._table,
            fields=fields,
            unique=False,
            name=index_name,
        )

    @api.model_create_multi
    def create(self, value_list):
        """Overridden method 'create'"""

        result = super().create(value_list)

        training_action_ids = result._get_training_action_ids()
        self._normalize_sequence(training_action_ids)

        return result

    def write(self, values):
        """Overridden method 'write'"""

        before_ids = set(self._get_training_action_ids())

        result = super().write(values)

        after_ids = set(self._get_training_action_ids())
        training_action_ids = list(before_ids | after_ids)

        self._normalize_sequence(training_action_ids)

        return result

    def unlink(self):
        """Overridden method 'unlink'"""

        training_action_ids = self._get_training_action_ids()

        result = super().unlink()

        self._normalize_sequence(training_action_ids)

        return result

    # -- Auxiliary methods ----------------------------------------------------

    def _get_training_action_ids(self):
        return self.mapped("training_action_id").ids or []

    @api.model
    def _normalize_sequence(self, training_action_ids=None):
        """
        Reassign facility link sequences for given training actions.

        This method ensures that all records in
        `academy_training_action_facility_link` related to the provided
        training actions have a strictly consecutive `sequence` value
        starting from 1. Ordering is based first on the current `sequence`
        (nulls last) and then by record `id` to keep a stable result.

        Args:
            training_action_ids (list[int] | None): list of training
                action IDs to normalize. If None or empty, no update is
                performed.
        """
        if not training_action_ids:
            return

        sql = """
            WITH ranked AS (
              SELECT
                "id" AS link_id,
                ROW_NUMBER() OVER (wnd) AS new_sequence
              FROM academy_training_action_facility_link
              WHERE training_action_id = ANY(%s)
              WINDOW wnd AS (
                PARTITION BY training_action_id
                ORDER BY "sequence" NULLS LAST, "id" ASC
              )
            )
            UPDATE academy_training_action_facility_link AS link
            SET "sequence" = ranked.new_sequence
            FROM ranked
            WHERE ranked.link_id = link."id"
        """

        self.env.cr.execute(sql, (training_action_ids,))

    @staticmethod
    def _real_id(record_set, single=False):
        """Return a list with no NewId's of a single no NewId"""

        result = []

        if record_set and single:
            record_set.ensure_one()

        for record in record_set:
            if isinstance(record.id, models.NewId):
                result.append(record._origin.id)
            else:
                result.append(record.id)

        if single:
            result = result[0] if len(result) == 1 else None

        return result
