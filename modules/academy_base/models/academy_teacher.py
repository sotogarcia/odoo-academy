###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################


from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval

from ..utils.helpers import (
    one2many_count,
    one2many_count_search_domain,
)


class AcademyTeacher(models.Model):
    """A teacher is a partner who can be enrolled on training actions"""

    _name = "academy.teacher"
    _description = "Academy teacher"

    _inherit = [  # noqa: RUF012
        "academy.support.staff",
    ]

    _order = "complete_name ASC, id DESC"

    _rec_name = "complete_name"
    _rec_names_search = [  # noqa: RUF012
        "complete_name",
        "email",
        "vat",
        "company_registry",
    ]

    assignment_ids = fields.One2many(
        string="Assignments",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="Training actions or actions lines assigned to this teacher.",
        comodel_name="academy.training.teacher.assignment",
        inverse_name="teacher_id",
        domain=[],
        context={},
        auto_join=False,
    )

    assignment_count = fields.Integer(
        string="No. of assignments",
        required=False,
        readonly=True,
        index=False,
        default=0,
        help=False,
        compute="_compute_assignment_count",
        search="_search_assignment_count",
    )

    @api.depends("assignment_ids")
    def _compute_assignment_count(self):
        counts = one2many_count(self, "assignment_ids")

        for record in self:
            record.assignment_count = counts.get(record.id, 0)

    @api.model
    def _search_assignment_count(self, operator, value):
        return one2many_count_search_domain(
            self,
            "assignment_ids",
            operator,
            value,
        )

    # -- Methods overrides ----------------------------------------------------

    @api.model
    def _get_relevant_category_external_id(self):
        return "academy_base.res_partner_category_teacher"

    # -- Public methods -------------------------------------------------------

    def view_assignments(self):
        self.ensure_one()

        action_xid = "academy_base.action_teacher_assignment_act_window"
        act_wnd = self.env.ref(action_xid)

        name = self.env._("Assignments: {}").format(self.display_name)

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))
        context.update({"default_teacher_id": self.id})

        domain = [("teacher_id", "=", self.id)]

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": act_wnd.res_model,
            "target": "current",
            "name": name,
            "view_mode": act_wnd.view_mode,
            "domain": domain,
            "context": context,
            "search_view_id": act_wnd.search_view_id.id,
            "help": act_wnd.help,
        }

        return serialized
