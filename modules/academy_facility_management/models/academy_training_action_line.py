# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.tools import safe_eval

from logging import getLogger


_logger = getLogger(__name__)


class AcademyCompetencyUnit(models.Model):
    """Allow to assign several facilities to the action line"""

    _name = "academy.training.action.line"
    _inherit = ["academy.training.action.line"]

    facility_assignment_ids = fields.One2many(
        string="Facility assignments",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Facilities used for teaching this program unit",
        comodel_name="academy.training.action.facility.link",
        inverse_name="action_line_id",
        domain=[],
        context={},
        auto_join=False,
        limit=None,
    )

    facility_ids = fields.Many2manyView(
        string="Facilities",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name="facility.facility",
        relation="academy_training_action_facility_link",
        column1="action_line_id",
        column2="facility_id",
        domain=[],
        context={},
        limit=None,
    )

    facility_count = fields.Integer(
        string="Facility count",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help="Number of facilities used for teaching this program unit",
        compute="_compute_facility_count",
    )

    @api.depends("facility_ids")
    def _compute_facility_count(self):
        for record in self:
            record.facility_count = len(record.facility_assignment_ids)

    def view_facility_assignments(self):
        self.ensure_one()

        action_xid = (
            "academy_facility_management.action_academy_training_"
            "action_facility_link_act_window"
        )
        act_wnd = self.env.ref(action_xid)

        name = self._truncate(self.name, 12, 24)

        training_id = self.env.context.get("default_training_action_id", -1)
        if not training_id:
            msg = _("No training action has been selected")
            raise UserError(msg)

        context = safe_eval(act_wnd.context)
        context.update(
            {
                "default_action_line_id": self.id,
                "default_training_action_id": training_id,
            }
        )

        domain = [
            ("action_line_id", "=", self.id),
            ("training_action_id", "=", training_id),
        ]

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": "academy.training.action.facility.link",
            "target": "current",
            "name": _("Facilities for {}").format(name),
            "view_mode": act_wnd.view_mode,
            "domain": domain,
            "context": context,
            "search_view_id": act_wnd.search_view_id.id,
            "help": act_wnd.help,
        }

        return serialized
