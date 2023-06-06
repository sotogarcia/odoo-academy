# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools import safe_eval
from odoo.osv.expression import FALSE_DOMAIN, TRUE_DOMAIN
from odoo.osv.expression import TERM_OPERATORS_NEGATION

from datetime import timedelta

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingAction(models.Model):
    """ Button to open session calendar
    """

    _name = 'academy.training.action'
    _inherit = ['academy.training.action']

    session_ids = fields.One2many(
        string='Sessions',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='All sessions for training action',
        comodel_name='academy.training.session',
        inverse_name='training_action_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    session_count = fields.Integer(
        string='Session count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of sessions on which the calculation has been made',
        compute='_compute_session_count',
        search='search_session_count'
    )

    @api.depends('session_ids')
    def _compute_session_count(self):
        for record in self:
            record.session_count = len(record.session_ids)

    @api.model
    def search_session_count(self, operator, value):
        sql = '''
            SELECT
                ata."id" AS training_action_id,
                COUNT ( ats."id" ) :: INTEGER AS session_count
            FROM
                academy_training_action AS ata
            LEFT JOIN academy_training_session AS ats
                ON ats.training_action_id = ata."id" AND ats.active
            GROUP BY
                ata."id"
            HAVING COUNT ( ats."id" ) :: INTEGER {operator} {value}
        '''

        # = True, <> True, = False, <> False
        if value in [True, False]:
            if value is True:
                operator = TERM_OPERATORS_NEGATION[operator]
            value = 0

        sql = sql.format(operator=operator, value=value)
        self.env.cr.execute(sql)
        results = self.env.cr.dictfetchall()

        if results:
            record_ids = [item['training_action_id'] for item in results]
            domain = [('id', 'in', record_ids)]
        else:
            domain = FALSE_DOMAIN

        return domain

    draft_count = fields.Integer(
        string='Draft count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of sessions in draft state',
        compute='_compute_draft_count',
        search='search_draft_count'
    )

    @api.depends('session_ids')
    def _compute_draft_count(self):
        for record in self:
            filtered_set = record.session_ids.filtered(
                lambda x: x.state == 'draft')
            record.draft_count = len(filtered_set)

    @api.model
    def search_draft_count(self, operator, value):
        sql = '''
            SELECT
                ata."id" AS training_action_id,
                COUNT ( ats."id" ) :: INTEGER AS session_count
            FROM
                academy_training_action AS ata
            LEFT JOIN academy_training_session AS ats
                ON ats.training_action_id = ata."id"
                AND ats.active AND ats."state" = 'draft'
            GROUP BY
                ata."id"
            HAVING COUNT ( ats."id" ) :: INTEGER {operator} {value}
        '''

        # = True, <> True, = False, <> False
        if value in [True, False]:
            if value is True:
                operator = TERM_OPERATORS_NEGATION[operator]
            value = 0

        sql = sql.format(operator=operator, value=value)
        self.env.cr.execute(sql)
        results = self.env.cr.dictfetchall()

        if results:
            record_ids = [item['training_action_id'] for item in results]
            domain = [('id', 'in', record_ids)]
        else:
            domain = FALSE_DOMAIN

        return domain

    allow_overlap = fields.Boolean(
        string='Allow overlap',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check to allow sessions for this training action to be overlapped'
    )

    def view_timesheets(self):
        action_xid = ('academy_timesheets.'
                      'action_academy_training_action_timesheet_act_window')
        action = self.env.ref(action_xid)

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.context))

        if self:
            domain = [('training_action_id', 'in', self.mapped('id'))]
        else:
            domain = TRUE_DOMAIN

        serialized = {
            'type': 'ir.actions.act_window',
            'res_model': action.res_model,
            'target': action.target,
            'name': action.name,
            'view_mode': action.view_mode,
            'domain': domain,
            'context': ctx,
            'search_view_id': action.search_view_id.id,
            'help': action.help
        }

        return serialized

    def view_sessions(self):
        self.ensure_one()

        action_xid = 'academy_timesheets.action_sessions_act_window'
        action = self.env.ref(action_xid)

        # Replace calendar view
        calendar_view_xid = ('academy_timesheets.view_academy_training_'
                             'session_calendar_no_training')
        views = self._updated_views(action, calendar_view_xid)

        name = _('Sessions for {}').format(self.action_name)

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.context))
        ctx.update({'default_training_action_id': self.id})

        domain = [('training_action_id', '=', self.id)]

        serialized = {
            'type': 'ir.actions.act_window',
            'res_model': 'academy.training.session',
            'target': 'current',
            'name': name,
            'view_mode': action.view_mode,
            'domain': domain,
            'context': ctx,
            'search_view_id': action.search_view_id.id,
            'help': action.help,
            'views': views
        }

        return serialized

    def copy_weekly_sessions(self, invite_all=True):
        now = fields.Datetime.now()
        now = now.replace(hour=0, minute=0, second=0, microsecond=0)

        week_start = now - timedelta(days=now.weekday())
        next_week_start = week_start + timedelta(days=7)

        action_ids = self.mapped('id')

        session_domain = [
            '&',
            ('training_action_id', 'in', action_ids),
            '|',
            '&',
            ('date_start', '>=', week_start),
            ('date_start', '<', next_week_start),
            '&',
            ('date_stop', '>=', week_start),
            ('date_stop', '<', next_week_start)
        ]
        session_obj = self.env['academy.training.session']
        session_set = session_obj.search(session_domain)

        target_set = session_set.copy_all()
        if invite_all:
            target_set.invite_all()

        return target_set

    def _updated_views(self, action, xid):
        views = [list(view) for view in action.views]
        view = self.env.ref(xid)

        for index in range(0, len(views)):
            if views[index][1] == view.type:
                views[index][0] = view.id

        return views

    def get_reference(self):
        """ Required by clone wizard

        Returns:
            str: model,id
        """

        self.ensure_one()

        return '{},{}'.format(self._name, self.id)
