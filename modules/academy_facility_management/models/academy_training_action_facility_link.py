# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.osv.expression import TRUE_DOMAIN
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

    _sql_constraints = [
        (
            "unique_training_action_facility",
            "UNIQUE(training_action_id, facility_id)",
            "Facility already has been set to this training action",
        )
    ]

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
