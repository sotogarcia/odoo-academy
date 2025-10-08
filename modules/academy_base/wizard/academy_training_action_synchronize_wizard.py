# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from ..utils.record_utils import get_active_records
from ..utils.helpers import OPERATOR_MAP, many2many_count
from odoo.osv.expression import TRUE_DOMAIN, FALSE_DOMAIN

from logging import getLogger

_logger = getLogger(__name__)


class AcademyTrainingActionSynchronizeWizard(models.TransientModel):
    _name = "academy.training.action.synchronize.wizard"
    _description = "Academy training action synchronize wizard"

    _rec_name = "display_name"
    _order = "id ASC"

    training_action_ids = fields.Many2many(
        string="Training actions",
        required=False,
        readonly=False,
        index=False,
        default=lambda self: get_active_records(
            self.env, "academy.training.action"
        ),
        help="Training actions whose program will be synchronized",
        comodel_name="academy.training.action",
        relation="academy_training_action_synchronize_wizard_action_rel",
        column1="wizard_id",
        column2="training_action_id",
        domain=[],
        context={},
    )

    training_action_count = fields.Integer(
        string="Number of training actions",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help="Computed number of training actions",
        compute="_compute_training_action_count",
        search="_search_training_action_count",
    )

    @api.depends("training_action_ids")
    def _compute_training_action_count(self):
        counts = many2many_count(self, "training_action_ids")

        for record in self:
            record.training_action_count = counts.get(record.id, 0)

    @api.model
    def _search_training_action_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = many2many_count(self.search([]), "training_action_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    create_new = fields.Boolean(
        string="Create new",
        required=False,
        readonly=False,
        index=False,
        default=False,
        help="Create missing training action lines",
    )

    update_existing = fields.Boolean(
        string="Update existing",
        required=False,
        readonly=False,
        index=False,
        default=False,
        help="Update existing training action lines",
    )

    remove_obsolete = fields.Boolean(
        string="Remove obsolete",
        required=False,
        readonly=False,
        index=False,
        default=False,
        help="Remove action lines that do not exist in the source program",
    )

    include_optional = fields.Boolean(
        string="Include optional",
        required=False,
        readonly=False,
        index=False,
        default=False,
        help="Include optional program action lines when creating new",
    )

    @api.depends("training_action_ids")
    @api.depends_context("lang")
    def _compute_display_name(self):
        pattern = _("Synchronize %s actions")
        for record in self:
            record.display_name = pattern % len(record.training_action_ids)

    def _compute_mode(self):
        self.ensure_one()

        mode = 0

        if self.create_new:
            mode += 0b0001
        if self.update_existing:
            mode += 0b0100
        if self.remove_obsolete:
            mode += 0b1000

        return mode

    def _perform_action(self):
        training_actions = self.training_action_ids

        mode = self._compute_mode()
        add_optional = self.include_optional

        training_actions.synchronize_from_program(mode, add_optional)

    def perform_action(self):
        for record in self:
            self._perform_action()
