# -*- coding: utf-8 -*-
""" AcademyCompetencyUnit

This module contains the academy.competency.unit Odoo model which stores
all competency unit attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools import safe_eval
from odoo.exceptions import UserError

from logging import getLogger

_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyCompetencyUnit(models.Model):
    """Competency unit stores the specific name will be used by a module in
    a training activity
    """

    _name = "academy.competency.unit"
    _description = "Academy competency unit"

    _rec_name = "competency_name"
    _order = "sequence ASC, competency_name ASC"

    _inherits = {"academy.training.module": "training_module_id"}

    _inherit = ["academy.abstract.training"]

    competency_code = fields.Char(
        string="Unit code",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Reference code that identifies the competency unit",
        size=30,
        translate=False,
    )

    competency_name = fields.Char(
        string="Competency name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Enter new name",
        size=1024,
        translate=True,
    )

    description = fields.Text(
        string="Description",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Enter new description",
        translate=True,
    )

    active = fields.Boolean(
        string="Active",
        required=False,
        readonly=False,
        index=False,
        default=True,
        help="Enables/disables the record",
    )

    sequence = fields.Integer(
        string="Sequence",
        required=True,
        readonly=False,
        index=False,
        default=0,
        help="Choose this competency unit order position",
    )

    training_module_id = fields.Many2one(
        string="Training module",
        required=True,
        readonly=False,
        index=False,
        default=None,
        help="Training module associated with this competency unit",
        comodel_name="academy.training.module",
        domain=[("training_module_id", "=", False)],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    training_activity_id = fields.Many2one(
        string="Training activity",
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name="academy.training.activity",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    professional_qualification_id = fields.Many2one(
        string="Academy professional qualification",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name="academy.professional.qualification",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    teacher_assignment_ids = fields.One2many(
        string="Teacher assignments",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Teachers who teach this competency unit",
        comodel_name="academy.competency.unit.teacher.rel",
        inverse_name="competency_unit_id",
        domain=[],
        context={},
        auto_join=False,
    )

    teacher_ids = fields.Many2manyView(
        string="Teachers",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name="academy.teacher",
        relation="academy_competency_unit_teacher_rel",
        column1="competency_unit_id",
        column2="teacher_id",
        domain=[],
        context={},
        copy=False,
    )

    teacher_count = fields.Integer(
        string="Teacher count",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help="Number of teachers who teach this competency unit",
        compute="_compute_teacher_count",
    )

    @api.depends("teacher_ids")
    def _compute_teacher_count(self):
        for record in self:
            record.teacher_count = len(record.teacher_assignment_ids)

    _sql_constraints = [
        (
            "unique_module_by_activity",
            "UNIQUE(training_activity_id, training_module_id)",
            "The module cannot be duplicated in the same training activity",
        )
    ]

    # -------------------------- OVERLOADED METHODS ---------------------------

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        """Prevents new record of the inherited (_inherits) model will be
        created
        """

        default = dict(default or {})
        default.update({"training_module_id": self.training_module_id.id})

        rec = super(AcademyCompetencyUnit, self).copy(default)
        return rec

    @staticmethod
    def _truncate(sz, minimum, maximum):
        if len(sz) > maximum:
            ls = max(minimum, sz.rfind(" "))
            sz = "{}...".format(sz[:ls])

        return sz

    def view_teacher_assignments(self):
        self.ensure_one()

        action_xid = "action_academy_competency_unit_teacher_rel_act_window"
        act_wnd = self.env.ref("academy_base.{}".format(action_xid))

        name = self._truncate(self.competency_name, 12, 24)

        training_id = self.env.context.get("default_training_action_id", -1)
        if not training_id:
            msg = _("No training action has been selected")
            raise UserError(msg)

        context = safe_eval(act_wnd.context)
        context.update(
            {
                "default_competency_unit_id": self.id,
                "default_training_action_id": training_id,
            }
        )

        domain = [
            ("competency_unit_id", "=", self.id),
            ("training_action_id", "=", training_id),
        ]

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": "academy.competency.unit.teacher.rel",
            "target": "current",
            "name": _("Teachers for {}").format(name),
            "view_mode": act_wnd.view_mode,
            "domain": domain,
            "context": context,
            "search_view_id": act_wnd.search_view_id.id,
            "help": act_wnd.help,
        }

        return serialized

    def go_to_module(self):
        module_set = self.mapped("training_module_id")

        if not module_set:
            msg = _("There is no training modules")
            raise UserError(msg)
        else:
            view_act = {
                "type": "ir.actions.act_window",
                "res_model": "academy.training.module",
                "target": "current",
                "nodestroy": True,
                "domain": [("id", "in", module_set.mapped("id"))],
            }

            if len(module_set) == 1:
                view_act.update(
                    {
                        "name": module_set.name,
                        "view_mode": "form",
                        "res_id": module_set.id,
                        "view_type": "form",
                    }
                )

            else:
                view_act.update(
                    {
                        "name": _("Modules"),
                        "view_mode": "kanban,list,form",
                        "res_id": None,
                        "view_type": "form",
                    }
                )

            return view_act
