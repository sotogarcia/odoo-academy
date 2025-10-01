# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingSessionTeacherRel(models.Model):
    """ """

    _name = "academy.training.session.teacher.rel"
    _description = "Academy training session teacher rel"

    _rec_name = "id"
    _order = "session_id DESC, sequence ASC"

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

    email = fields.Char(string="Email", related="teacher_id.email")

    phone = fields.Char(string="Phone", related="teacher_id.phone")

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

    _sql_constraints = [
        (
            "UNIQUE_TEACHER_BY_SESSION",
            "UNIQUE(session_id, teacher_id)",
            "The teacher had already been assigned to the session",
        ),
        (
            "unique_teacher_id",
            """EXCLUDE USING gist (
                teacher_id WITH =,
                tsrange ( date_start, date_stop ) WITH &&
            ) WHERE (validate); -- Requires btree_gist""",
            "This teacher is occupied by another training action",
        ),
    ]

    @api.model
    def create(self, values):
        """Overridden method 'create'"""

        parent = super(AcademyTrainingSessionTeacherRel, self)
        result = parent.create(values)

        result._update_session_followers()

        return result

    def write(self, values):
        """Overridden method 'write'"""

        parent = super(AcademyTrainingSessionTeacherRel, self)
        result = parent.write(values)

        self._update_session_followers()

        return result

    def _update_session_followers(self):
        path = "teacher_id.res_users_id.partner_id.id"

        for record in self:
            session = record.session_id

            if session.state == "ready":
                partner_ids = record.mapped(path)
                session.message_subscribe(partner_ids=partner_ids)
