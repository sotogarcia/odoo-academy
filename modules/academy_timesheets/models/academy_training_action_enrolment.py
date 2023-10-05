# -*- coding: utf-8 -*-
""" AcademyTrainingActionEnrolment

This module contains the academy.training.action.enrolment Odoo model which
stores all training action enrolment attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools import safe_eval
from odoo.osv.expression import AND

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingActionEnrolment(models.Model):
    """ Automatriculate students
    """

    _inherit = ['academy.training.action.enrolment']

    invitation_ids = fields.One2many(
        string='Invitation',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='List of current invitations for the enrolment',
        comodel_name='academy.training.session.invitation',
        inverse_name='enrolment_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    invitation_count = fields.Integer(
        string='Invitation count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of students have been invited to the enrolment',
        compute='_compute_invitation_count',
        store=False
    )

    @api.depends('invitation_ids')
    def _compute_invitation_count(self):
        for record in self:
            record.invitation_count = len(record.invitation_ids)

    exclusion_ids = fields.One2many(
        string='Exclusions',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Pendent training session invitations',
        comodel_name='academy.training.session.affinity',
        inverse_name='enrolment_id',
        domain=[("invited", "<>", True)],
        context={},
        auto_join=False,
        limit=None
    )

    exclusion_count = fields.Integer(
        string='Exclusion count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of pendent invitations',
        compute='_compute_exclusion_count',
        store=False
    )

    @api.depends('exclusion_ids')
    def _compute_exclusion_count(self):
        for record in self:
            record.exclusion_count = len(record.exclusion_ids)

    @api.model
    def create(self, values):
        """ Overridden method 'create'
        """

        parent = super(AcademyTrainingActionEnrolment, self)
        result = parent.create(values)

        result._link_pendent_invitations()

        return result

    def write(self, values):
        """ Overridden method 'write'
        """

        major_changes = self._will_be_drastically_changed(values)
        if major_changes:
            values['invitation_ids'] = [(5, None, None)]

        parent = super(AcademyTrainingActionEnrolment, self)
        result = parent.write(values)

        if not major_changes:
            self._unlink_expired_invitations(values)

        self._link_pendent_invitations()

        return result

    def view_invitation(self):
        self.ensure_one()

        action_xid = 'academy_timesheets.action_invitation_act_window'
        action = self.env.ref(action_xid)

        ctx = {'default_enrolment_id': self.id}
        domain = [('enrolment_id', '=', self.id)]

        serialized = {
            'type': 'ir.actions.act_window',
            'res_model': 'academy.training.session.invitation',
            'target': 'current',
            'name': _('Invitations'),
            'view_mode': action.view_mode,
            'domain': domain,
            'context': ctx,
            'search_view_id': action.search_view_id.id,
            'help': action.help
        }

        return serialized

    def view_exclusion(self):
        self.ensure_one()

        action_xid = 'academy_timesheets.action_affinity_act_window'
        action = self.env.ref(action_xid)

        ctx = {'default_enrolment_id': self.id}
        domain = [
            ('enrolment_id', '=', self.id),
            ("invited", "<>", True)
        ]

        serialized = {
            'type': 'ir.actions.act_window',
            'res_model': 'academy.training.session.affinity',
            'target': 'current',
            'name': _('Exclusions'),
            'view_mode': action.view_mode,
            'domain': domain,
            'context': ctx,
            'search_view_id': action.search_view_id.id,
            'help': action.help
        }

        return serialized

    @staticmethod
    def _will_be_drastically_changed(values):
        """ If the student or the training action are changed, it means that
        the enrolment was wrong and that it is being replaced by a new one.

        Args:
            values (dict): write ``values`` dictionary

        Returns:
            bool: True if student or training action are in values
        """

        return 'student_id' in values or 'training_action_id' in values

    @staticmethod
    def _pick_up_dates(values):

        register = values.get('register', False)
        if register:
            register = fields.Datetime.from_string(register)

        deregister = values.get('deregister', False)
        if deregister:
            deregister = fields.Datetime.from_string(deregister)

        return register, deregister

    def _unlink_expired_invitations(self, values):
        unlink_set = self.env['academy.training.session.invitation']

        invitation_set = self.mapped('invitation_ids')
        register, deregister = self._pick_up_dates(values)

        if register:
            unlink_set += invitation_set.filtered(
                lambda x: x.date_stop <= register)

        if deregister:
            unlink_set += invitation_set.filtered(
                lambda x: x.date_start >= deregister)

        unlink_set.unlink()

    def _link_pendent_invitations(self):
        # for record in self:
        #     domains = []

        #     training_action_id = record.training_action_id.id

        #     domains.append([('training_action_id', '=', training_action_id)])
        #     domains.append([('date_stop', '>', record.register)])
        #     if record.deregister:
        #         domains.append([("date_start", "<", record.deregister)])

        #     session_domain = AND(domains)
        #     session_obj = record.env['academy.training.session']
        #     session_set = session_obj.search(session_domain)

        #     session_set.invite_all()
        #
        affinity_obj = self.env['academy.training.session.affinity']
        for record in self:
            domain = [
                ('enrolment_id', '=', record.id),
                ('invited', '!=', True)
            ]
            affinity_set = affinity_obj.search(domain)
            affinity_set.toggle_invitation()
