# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.osv.expression import NEGATIVE_TERM_OPERATORS
from odoo.exceptions import ValidationError
from psycopg2.errors import RaiseException as PsqlException
from odoo.addons.academy_base.utils.sql_helpers import process_psql_exception

from logging import getLogger


_logger = getLogger(__name__)


class FacilityReservation(models.Model):
    """ """

    _name = "facility.reservation"
    _inherit = ["facility.reservation"]

    session_id = fields.Many2one(
        string="Session",
        required=False,
        readonly=False,
        index=True,
        default=None,
        help="Session to which this facility reservation is related",
        comodel_name="academy.training.session",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    has_training_session = fields.Boolean(
        string="Has training session",
        required=False,
        readonly=True,
        index=False,
        default=False,
        help="Check it when the reservation has a related training session",
        compute="_compute_has_training_session",
        search="_search_has_training_session",
    )

    @api.depends("session_id")
    def _compute_has_training_session(self):
        for record in self:
            record.has_training_session = bool(record.session_id)

    @api.model
    def _search_has_training_session(self, operator, value):
        value = bool(value)  # Prevents None

        if value is True:
            operator = NEGATIVE_TERM_OPERATORS(operator)
            value = not value

        return [("session_id", operator, value)]

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
            "UNIQUE_FACILITY_BY_SESSION",
            "UNIQUE(facility_id, session_id)",
            "The facility had already been assigned to the session",
        ),
        (
            "positive_interval",  # Overwrite original
            "CHECK(session_id IS NOT NULL OR (date_start < date_stop))",
            "Reservation cannot finish before it starts",
        ),
    ]

    def _notify_record_by_email(
        self,
        message,
        recipients_data,
        msg_vals=False,
        model_description=False,
        mail_auto_delete=True,
        check_existing=False,
        force_send=True,
        send_after_commit=True,
        **kwargs
    ):
        # Try to prevent reservations linked to ``draft`` sessions from
        # notifying users by email
        if (
            self
            and len(self) == 1
            and self.session_id
            and self.session_id.state == "draft"
        ):
            return True

        parent = super(FacilityReservation, self)
        return parent._notify_record_by_email(
            message,
            recipients_data,
            msg_vals,
            model_description,
            mail_auto_delete,
            check_existing,
            force_send,
            send_after_commit,
            **kwargs
        )

    # def _write(self, values):
    #     """ Overridden method 'write' to catch trigger exceptions
    #     """

    #     parent = super(FacilityReservation, self)

    #     try:
    #         result = parent._write(values)
    #     except PsqlException as ex:
    #         if str(ex.pgcode) == 'P0001':
    #             values = process_psql_exception(ex)
    #             error = values.get('error', False)
    #             if error:
    #                 raise ValidationError(error)
    #         else:
    #             raise

    #     return result

    # @api.model
    # def _create(self, values):
    #     """ Overridden method 'create'
    #     """

    #     parent = super(FacilityReservation, self)
    #     try:
    #         result = parent._create(values)
    #     except PsqlException as ex:
    #         if str(ex.pgcode) == 'P0001':
    #             values = process_psql_exception(ex)
    #             error = values.get('error', False)
    #             if error:
    #                 raise ValidationError(error)
    #         else:
    #             raise

    #     return result

    def detach_from_training(self):
        self.write({"session_id": None})

    @api.model
    def create(self, values):
        """Overridden method 'create'"""
        self._keep_in_sync_training_action(values)

        parent = super(FacilityReservation, self)
        result = parent.create(values)

        return result

    def write(self, values):
        """Overridden method 'write'"""

        self._keep_in_sync_training_action(values)

        parent = super(FacilityReservation, self)
        result = parent.write(values)

        return result

    @api.model
    def _keep_in_sync_training_action(self, values, keep_on_remove=False):
        """
        Synchronize the ``training_action_id`` field with the ``session_id``
        field in the record.

        When a ``session_id`` is provided in the values, this method updates
        the ``training_action_id`` field to match the ``training_action_id`` of
        the session. If the ``session_id`` is removed (or set to False), the
        ``training_action_id`` is also cleared unless ``keep_on_remove`` is
        True.

        Args:
            values (dict): A dictionary containing the fields to be updated.
            keep_on_remove (bool, optional): If True, keeps the current
                training_action_id when the session_id is removed. Defaults to
                False.
        """

        if "session_id" in values:
            session_id = values.get("session_id", False)

            if session_id:
                model_obj = self.env["academy.training.session"]
                model_set = model_obj.browse(session_id)
                values["training_action_id"] = model_set.training_action_id.id

            elif not keep_on_remove:
                values["training_action_id"] = None
