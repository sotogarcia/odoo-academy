# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools import safe_eval

from logging import getLogger
from urllib.parse import urljoin


_logger = getLogger(__name__)


class AcademyTeacher(models.Model):
    """ Button to open session calendar
    """

    _inherit = ['academy.teacher']

    session_ids = fields.Many2manyView(
        string='Sessions',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Sessions that this professor will participate in',
        comodel_name='academy.training.session',
        relation='academy_training_session_teacher_rel',
        column1='teacher_id',
        column2='session_id',
        domain=[],
        context={},
        limit=None
    )

    session_count = fields.Integer(
        string='Session count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of related sessions',
        compute='_compute_session_count'
    )

    @api.depends('session_ids')
    def _compute_session_count(self):
        for record in self:
            target = record.session_ids.filtered(
                lambda x: x.date_stop >= fields.Datetime.now())
            record.session_count = len(target)

    schedule_url = fields.Char(
        string='Schedule URL',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Compute base report URL',
        size=2048,
        translate=False,
        compute='_compute_schedule_url'
    )

    def _compute_schedule_url(self):
        """ This will be used in a email template. The URL will be always the
        same, but it must be gotten from ir.config_parameter.
        """
        config = self.env['ir.config_parameter'].sudo()
        base_url = config.get_param('web.base.url')
        url = urljoin(base_url, '/academy-timesheets/teacher/schedule')

        for record in self:
            record.schedule_url = url

    def _compute_view_mapping(self):
        view_names = [
            'view_academy_training_session_calendar_no_primary_instructor',
            'view_academy_training_session_kanban',
            'view_academy_training_session_tree',
            'view_academy_training_session_pivot',
            'view_academy_training_session_form'
        ]

        view_mapping = []
        for view_name in view_names:
            xid = 'academy_timesheets.{}'.format(view_name)
            view = self.env.ref(xid)
            pair = (view.id, view.type)
            view_mapping.append(pair)

        return view_mapping

    def view_sessions(self):
        self.ensure_one()

        action_xid = 'academy_timesheets.action_sessions_act_window'
        action = self.env.ref(action_xid)

        name = _('Sessions taught by {}').format(self.name)

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.context))
        ctx.update({'default_primary_teacher_id': self.id})

        domain = [('teacher_ids', '=', self.id)]

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
            'views': self._compute_view_mapping()
        }

        return serialized

    def get_reference(self):
        """ Required by clone wizard

        Returns:
            str: model,id
        """

        self.ensure_one()

        return '{},{}'.format(self._name, self.id)
