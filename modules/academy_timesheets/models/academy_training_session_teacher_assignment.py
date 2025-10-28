# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingSessionTeacherAssignment(models.Model):
    """ """

    _name = "academy.training.session.teacher.assignment"
    _description = "Academy training session teacher rel"

    _rec_name = "id"
    _order = "session_id DESC, sequence ASC"
    _rec_names_search = ["name", "code", "training_program_id"]

    # Entity fields
    # -------------------------------------------------------------------------

    teacher_id = fields.Many2one(
        string="Teacher",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Related teacher",
        comodel_name="academy.teacher",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    session_id = fields.Many2one(
        string="Session",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Related training session",
        comodel_name="academy.training.session",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    validate = fields.Boolean(
        string="Validate",
        help="If checked, the event date range will be checked before saving",
        related="session_id.validate",
        store=True,
    )

    sequence = fields.Integer(
        string="Sequence",
        required=True,
        readonly=False,
        index=True,
        default=0,
        help="Order of importance of the teacher in the training session",
    )

    # Student information
    # -------------------------------------------------------------------------

    email = fields.Char(string="Email", related="teacher_id.email")

    phone = fields.Char(string="Phone", related="teacher_id.call_number")

    # Session information
    # -------------------------------------------------------------------------

    date_start = fields.Datetime(
        string="Beginning",
        help="Date/time of session start",
        related="session_id.date_start",
        store=True,
    )

    date_stop = fields.Datetime(
        string="Ending",
        help="Date/time of session end",
        related="session_id.date_stop",
        store=True,
    )

    # Model constraints
    # -------------------------------------------------------------------------

    _sql_constraints = [
        (
            "unique_teacher_by_session",
            "UNIQUE(session_id, teacher_id)",
            "The teacher had already been assigned to the session",
        ),
        (
            "unique_teacher_id",
            """EXCLUDE USING gist (
                teacher_id gist_int4_ops WITH =,
                tsrange ( date_start, date_stop ) WITH &&
            ) WHERE (validate); -- Requires btree_gist""",
            "This teacher is occupied by another training action",
        ),
    ]

    # Methods overrides
    # -------------------------------------------------------------------------

    @api.depends("teacher_id", "session_id")
    @api.depends_context(
        "lang",
        "training_teacher_omit_teacher",
        "training_teacher_omit_session",
    )
    def _compute_display_name(self):
        _t = self.env._

        id_as_name = _t("Link session‒teacher: #%s")

        ctx = self.env.context
        show_teacher = not ctx.get("training_teacher_omit_teacher", False)
        show_session = not ctx.get("training_teacher_omit_session", False)

        for record in self:
            values = []

            if show_session:
                if record.session_id and record.session_id.display_name:
                    values.append(record.session_id.display_name)
                else:
                    values.append(_t("Unnamed"))

            if show_teacher:
                if record.teacher_id and record.teacher_id.display_name:
                    values.append(record.teacher_id.display_name)
                else:
                    values.append(_t("Anonymous"))

            if values:
                record.display_name = " ‒ ".join(values)
            elif isinstance(record.id, int):
                record.display_name = id_as_name % record.id
            else:
                record.display_name = _t("New link session‒teacher")

    @api.model_create_multi
    def create(self, value_list):
        """Overridden method 'create'"""

        result = super().create(value_list)

        result._update_session_followers()

        return result

    def write(self, values):
        """Overridden method 'write'"""

        result = super().write(values)

        self._update_session_followers()

        return result

    def _update_session_followers(self):
        path = "teacher_id.partner_id.id"

        for record in self:
            session = record.session_id

            if session.state == "ready":
                partner_ids = record.mapped(path)
                session.message_subscribe(partner_ids=partner_ids)
