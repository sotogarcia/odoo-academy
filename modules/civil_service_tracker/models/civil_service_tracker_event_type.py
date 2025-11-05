# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools import safe_eval

from logging import getLogger


_logger = getLogger(__name__)


class CivilServiceTrackerEventType(models.Model):
    _name = "civil.service.tracker.event.type"
    _description = "Civil service tracker event type"

    _table = "cst_event_type"

    _rec_name = "name"
    _order = "sequence ASC, name ASC"

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Name of the event type (e.g. Call, Exam)",
        translate=True,
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Additional details about this event type",
        translate=True,
    )

    active = fields.Boolean(
        string="Active",
        required=False,
        readonly=False,
        index=False,
        default=True,
        help="Uncheck to hide without deleting",
    )

    sequence = fields.Integer(
        string="Sequence",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Defines the display order",
    )

    is_stage = fields.Boolean(
        string="Is stage",
        required=False,
        readonly=False,
        index=False,
        default=False,
        help="Mark if this type represents a process stage",
    )

    all_day = fields.Boolean(
        string="All day",
        required=False,
        readonly=False,
        index=True,
        default=True,
        help="Indicates that this event spans the entire day",
    )

    unique = fields.Boolean(
        string="Unique",
        required=False,
        readonly=False,
        index=False,
        default=False,
        help="Only one event of this type per process is allowed",
    )

    fold = fields.Boolean(
        string="Fold",
        required=False,
        readonly=False,
        index=False,
        default=False,
        help="Folded by default in kanban view if used as stage",
    )

    related_field_id = fields.Many2one(
        string="Related field",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Virtual date field to link with this event",
        comodel_name="ir.model.fields",
        domain=[
            ("model", "=", "civil.service.tracker.selection.process"),
            ("ttype", "=", "date"),
            ("store", "=", False),
        ],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    process_event_ids = fields.One2many(
        string="Process events",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Events of this type registered in processes",
        comodel_name="civil.service.tracker.process.event",
        inverse_name="event_type_id",
        domain=[],
        context={},
        auto_join=False,
    )

    # - Field: process_event_count (compute)
    # ------------------------------------------------------------------------

    process_event_count = fields.Integer(
        string="Event count",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help="Number of events of this type",
        compute="_compute_process_event_count",
    )

    @api.depends("process_event_ids")
    def _compute_process_event_count(self):
        event_model = self.env["civil.service.tracker.process.event"]

        # Group by event_type_id and count how many events exist per type
        grouped = event_model.read_group(
            [("event_type_id", "in", self.ids)],
            ["event_type_id"],
            ["event_type_id"],
        )

        # Build a mapping: {event_type_id: event_count}
        count_map = {
            group["event_type_id"][0]: group["event_type_id_count"]
            for group in grouped
        }

        # Assign the count to each record, defaulting to 0 if missing
        for record in self:
            record.process_event_count = count_map.get(record.id, 0)

    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------

    _sql_constraints = [
        # 1. If related_field_id is set, then unique must be True
        (
            "check_related_field_requires_unique",
            'CHECK (related_field_id IS NULL OR "unique")',
            "An event type linked to a process field must be unique.",
        ),
        # 2. Name must be unique
        (
            "unique_event_type_name",
            "UNIQUE(name)",
            "Event type name must be unique.",
        ),
        # # 3. Name must have at least 3 characters
        # (
        #     'check_event_type_name_length',
        #     "CHECK (char_length(name) >= 3)",
        #     'Event type name must be at least 3 characters long.'
        # ),
    ]

    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------

    def view_process_events(self):
        self.ensure_one()

        action_xid = (
            "civil_service_tracker."
            "action_civil_services_selection_process_act_window"
        )
        act_wnd = self.env.ref(action_xid)

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))
        context.update({"default_event_type_id": self.id})

        domain = [("event_type_id", "=", self.id)]

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": act_wnd.res_model,
            "target": "current",
            "name": act_wnd.name,
            "view_mode": act_wnd.view_mode,
            "domain": domain,
            "context": context,
            "search_view_id": act_wnd.search_view_id.id,
            "help": act_wnd.help,
        }

        return serialized
