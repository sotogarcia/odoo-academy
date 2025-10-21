# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

# NOTE: Some fields use ``compute_sudo=True`` to prevent an extrange warning
# from using the same method to calculate stored and non-stored fields. See:
# https://github.com/odoo/odoo/issues/39306

from odoo import models, fields, api
from odoo.osv.expression import TRUE_DOMAIN, FALSE_DOMAIN
from odoo.osv.expression import OR
from odoo.addons.academy_base.utils.helpers import OPERATOR_MAP
from odoo.addons.academy_base.utils.helpers import many2many_count


from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingAction(models.Model):
    """ """

    _name = "academy.training.action"

    _inherit = ["academy.training.action"]

    facility_link_ids = fields.One2many(
        string="Facility links",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Required educational facilities in relevance order",
        comodel_name="academy.training.action.facility.link",
        inverse_name="training_action_id",
        domain=[("action_line_id", "=", False)],
        context={},
        auto_join=False,
    )

    facility_ids = fields.Many2manyView(
        string="Facilities",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help="Required educational facilities",
        comodel_name="facility.facility",
        relation="academy_training_action_facility_link",
        column1="training_action_id",
        column2="facility_id",
        domain=[],
        context={},
    )

    primary_facility_id = fields.Many2one(
        string="Primary facility",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Main educational facility",
        comodel_name="facility.facility",
        domain=[],
        context={},
        ondelete="restrict",
        auto_join=False,
        compute="_compute_primary_facility_id",
        search="_search_primary_facility_id",
        compute_sudo=True,
        store=True,
    )

    @api.depends(
        "facility_link_ids",
        "facility_link_ids.sequence",
        "facility_link_ids.facility_id",
    )
    def _compute_primary_facility_id(self):
        domain = [
            ("training_action_id", "in", self.ids),
            ("sequence", "!=", False),
        ]
        link_obj = self.env["academy.training.action.facility.link"]
        links = link_obj.search(
            domain,
            order="training_action_id, sequence asc, id asc",
        )

        first_by_action = {}
        for link in links:
            aid = link.training_action_id.id
            if aid not in first_by_action:
                first_by_action[aid] = link.facility_id.id

        for record in self:
            record.primary_facility_id = first_by_action.get(record.id, False)

    facility_count = fields.Integer(
        string="Facility count",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help="Number of facilities needed for this training action",
        compute="_compute_facility_count",
        search="_search_facility_count",
        compute_sudo=True,
    )

    @api.depends("child_ids")
    def _compute_facility_count(self):
        counts = many2many_count(self, "facility_ids")

        for record in self:
            record.facility_count = counts.get(record.id, 0)

    @api.model
    def _search_facility_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = many2many_count(self.search([]), "facility_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    primary_complex_id = fields.Many2one(
        string="Primary complex",
        related="primary_facility_id.complex_id",
        store=True,
    )
