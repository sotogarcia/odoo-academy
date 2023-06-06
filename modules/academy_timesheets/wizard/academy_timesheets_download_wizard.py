# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger
from odoo.exceptions import UserError
from urllib.parse import urljoin


_logger = getLogger(__name__)


class AcademyTimesheetsDownload(models.TransientModel):
    """ Download timesheets
    """

    _name = 'academy.timesheets.download.wizard'
    _description = u'Academy timesheets download'

    _rec_name = 'id'
    _order = 'id DESC'

    mime = fields.Selection(
        string='Format',
        required=True,
        readonly=False,
        index=False,
        default='pdf',
        help='Document file format',
        selection=[('pdf', 'PDF document'), ('html', 'Webpage')]
    )

    week = fields.Selection(
        string='Week',
        required=True,
        readonly=False,
        index=False,
        default='next',
        help='week corresponding to the schedule',
        selection=[
            ('last', 'Previous week'),
            ('current', 'Current week'),
            ('next', 'Next week'),
            ('other', 'Choose date')
        ]
    )

    week_date = fields.Date(
        string='Week date',
        required=False,
        readonly=False,
        index=False,
        default=lambda self: fields.Date.context_today(self),
        help='Date in the target week'
    )

    download = fields.Boolean(
        string='Download',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to force download timesheet document'
    )

    target_ref = fields.Reference(
        string='Target',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_target_ref(),
        help='Choose target elemento to download timesheet',
        selection=[
            ('academy.training.action', 'Training action'),
            ('academy.teacher', 'Teacher'),
            ('academy.student', 'Student')
        ]
    )

    url = fields.Char(
        string='URL',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='URL can be used to download document',
        size=2048,
        translate=False,
        compute='compute_url'
    )

    @api.depends('target_ref', 'download', 'mime', 'week', 'week_date')
    def compute_url(self):
        for record in self:
            if not record.target_ref:
                record.url = None
            else:
                base_url = record._get_base_url()
                relative_url = record._compute_relative_url()
                url = urljoin(base_url, relative_url)

                query_string = self._compute_query_string()

                record.url = url + query_string

    def default_target_ref(self):
        result = None

        active_model = self.env.context.get('active_model', False)
        if active_model:
            active_id = self.env.context.get('active_id', False)
            if active_id:
                result = self.env[active_model].browse(active_id)

        return result

    def _get_base_url(self):
        config = self.env['ir.config_parameter']
        return config.get_param('web.base.url')

    def _compute_relative_url(self):
        action_obj = self.env['academy.training.action']
        teacher_obj = self.env['academy.teacher']
        student_obj = self.env['academy.student']

        if isinstance(self.target_ref, type(action_obj)):
            url = '/academy-timesheets/training/{target_id}/schedule'
        elif isinstance(self.target_ref, type(teacher_obj)):
            url = '/academy-timesheets/teacher/{target_id}/schedule'
        elif isinstance(self.target_ref, type(student_obj)):
            url = '/academy-timesheets/student/{target_id}/schedule'
        else:
            raise UserError(_('Invalid target item'))

        return url.format(target_id=self.target_ref.id)

    def _compute_query_string(self):
        pattern = '?week={week}&format={mime}&download={download}'

        if self.week == 'other':
            week = self.week_date.strftime('%Y-%m-%d')
        else:
            week = self.week

        return pattern.format(
            week=week, mime=self.mime, download=self.download)

    def perform_action(self):
        self.ensure_one()

        return {
            'name': _('Scheduler document'),
            'res_model': 'ir.actions.act_url',
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.url
        }
