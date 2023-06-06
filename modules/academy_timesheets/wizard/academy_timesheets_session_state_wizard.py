# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class AcademyTimesheetSessionStateWizard(models.TransientModel):
    """ Wizard to change the state to several sessions at the same time
    """

    _name = 'academy.timesheet.session.state.wizard'
    _description = u'Academy timesheet session state wizard'

    _rec_name = 'id'
    _order = 'id ASC'

    session_ids = fields.Many2many(
        string='Sessions',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_session_ids(),
        help='Target sessions',
        comodel_name='academy.training.session',
        relation='academy_timesheet_session_state_wizard_rel',
        column1='wizard_id',
        column2='session_id',
        domain=[],
        context={},
        limit=None
    )

    state = fields.Selection(
        string='State',
        required=True,
        readonly=False,
        index=False,
        default='toggle',
        help='Choose new session status',
        selection=[
            ('toggle', 'Toggle'),
            ('draft', 'Draft'),
            ('ready', 'Ready')
        ]
    )

    session_count = fields.Integer(
        string='Session count',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help='Total number of sessions'
    )

    draft_count = fields.Integer(
        string='In draft',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help='Number of sessions in Draft state'
    )

    ready_count = fields.Integer(
        string='In ready',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help='Number of sessions in Ready state'
    )

    def default_session_ids(self):
        session_set = self.env['academy.training.session']

        active_model = self.env.context.get('active_model', None)
        if active_model == 'academy.training.session':
            active_ids = self.env.context.get('active_ids', [])
            if not active_ids:
                active_id = self.env.context('active_id', False)
                if active_id:
                    active_ids = [active_id]

            if active_ids:
                session_domain = [('id', 'in', active_ids)]
                session_set = session_set.search(session_domain)

        return session_set

    @api.onchange('session_ids')
    def _onchange_session_id(self):
        for record in self:
            states = record.mapped('session_ids.state')
            record.session_count = len(states)

            in_draft = [item for item in states if item == 'draft']
            in_ready = [item for item in states if item == 'ready']

            record.draft_count = len(in_draft)
            record.ready_count = len(in_ready)

            if record.draft_count > 0 and record.ready_count == 0:
                record.state = 'ready'
            elif record.draft_count == 0 and record.ready_count > 0:
                record.state = 'draft'
            else:
                record.state = 'toggle'

    def perform_action(self):
        self.ensure_one()

        state = self.state
        if state == 'toggle':
            self.session_ids.toogle_state()
        else:
            self.session_ids.write({'state': state})
