###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class AcademyStudentSignupStateTransition(models.Model):
    """State transition in the lifecycle of a student sign-up."""

    _name = "academy.student.signup.state.transition"
    _description = "Student sign-up state transition"

    _rec_name = "id"
    _order = "timestamp, id"

    signup_id = fields.Many2one(
        string="Sign-up",
        required=True,
        readonly=True,
        index=True,
        default=None,
        help="Student sign-up whose state changes at this transition.",
        comodel_name="academy.student.signup",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    state = fields.Selection(
        string="State",
        required=True,
        readonly=True,
        index=True,
        default=None,
        help="State reached by the student sign-up at this transition.",
        selection=[
            ("signed_up", "Signed up"),
            ("enrolled", "Enrolled"),
        ],
    )

    enrolment_id = fields.Many2one(
        string="Enrolment",
        required=True,
        readonly=True,
        index=True,
        default=None,
        help="Enrolment responsible for this state transition.",
        comodel_name="academy.training.action.enrolment",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    timestamp = fields.Datetime(
        string="Timestamp",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help="Effective date and time of this state transition.",
        compute="_compute_timestamp",
        store=True,
    )

    @api.depends(
        "state",
        "enrolment_id.register",
        "enrolment_id.deregister",
    )
    def _compute_timestamp(self):
        for transition in self:
            if transition.state == "enrolled":
                transition.timestamp = transition.enrolment_id.register
            else:
                transition.timestamp = transition.enrolment_id.deregister

    # -- Constraints ----------------------------------------------------------

    _sql_constraints = [  # noqa: RUF012
        (
            "unique_signup_state_enrolment",
            "UNIQUE(signup_id, state, enrolment_id)",
            "A state transition for this sign-up, state and enrolment already exists.",
        ),
    ]

    @api.constrains("signup_id", "enrolment_id")
    def _check_enrolment_signup(self):
        for transition in self:
            enrolment = transition.enrolment_id

            if enrolment and enrolment.signup_id != transition.signup_id:
                err = _("Enrolment must match state transition sign-up.")
                raise ValidationError(err)
