###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _


class AcademyStudentSignupStateTransition(models.Model):
    """State transition in the lifecycle of a student sign-up."""

    _name = "academy.student.signup.state.transition"
    _description = "Student sign-up state transition"

    _rec_name = "id"
    _order = "timestamp, id"

    # -- Fields ----------------------------------------------------------------

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
        copy=False,
    )

    previous_state = fields.Selection(
        string="Previous state",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help="State of the student sign-up before this transition.",
        copy=False,
        selection=[
            ("signed_up", "Signed up"),
            ("enrolled", "Enrolled"),
        ],
    )

    state = fields.Selection(
        string="State",
        required=True,
        readonly=True,
        index=True,
        default=None,
        help="State reached by the student sign-up at this transition.",
        copy=False,
        selection=[
            ("signed_up", "Signed up"),
            ("enrolled", "Enrolled"),
        ],
    )

    timestamp = fields.Datetime(
        string="Timestamp",
        required=True,
        readonly=True,
        index=True,
        default=fields.Datetime.now,
        help="Date and time when the state transition was recorded.",
        copy=False,
    )

    source_ref = fields.Reference(
        string="Source document",
        required=False,
        readonly=True,
        index=True,
        default=None,
        help="Document responsible for this state transition, when applicable.",
        copy=False,
        selection=[
            ("academy.training.action.enrolment", "Enrolment"),
        ],
    )

    # -- Constraints -----------------------------------------------------------

    @api.constrains("signup_id", "source_ref")
    def _check_source_signup(self):
        for transition in self:
            source = transition.source_ref

            if source and source.signup_id != transition.signup_id:
                err = _(
                    "Source document must belong to the transition sign-up."
                )
                raise ValidationError(err)

    # -- CRUD - quizá más tarde ------------------------------------------------

    # def write(self, values):
    #     raise UserError(_("State transitions cannot be modified."))

    # def unlink(self):
    #     raise UserError(_("State transitions cannot be deleted."))
