# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
from logging import getLogger


_logger = getLogger(__name__)


class AcademyPublicTenderingOffer(models.Model):
    """ The summary line for a class docstring should fit on one line.

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.public.tendering.public.offer'
    _description = u'Academy public tendering public offer'

    _inherit = ['image.mixin', 'mail.thread']

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=False,
        size=255,
        translate=True
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help=('If the active field is set to false, it will allow you '
              'to hide record without removing it.'),
        track_visibility='onchange'
    )

    public_administration_id = fields.Many2one(
        string='Administration',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose the administration related with tendering',
        comodel_name='academy.public.tendering.public.administration',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        track_visibility='always'
    )

    tendering_process_ids = fields.One2many(
        string='Processes',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.public.tendering.process',
        inverse_name='public_offer_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    bulletin_board_url = fields.Char(
        string='Bulletin Board',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='URL of the bulletin board',
        size=256,
        translate=True
    )

    official_journal_url = fields.Char(
        string='Official journal',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='URL of the article in the official journal',
        size=256,
        translate=True
    )

    total_of_vacancies = fields.Integer(
        string='Nº of vacancies',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Total number of vacancy positions',
        compute=lambda self: self._compute_total_of_vacancies()
    )

    total_of_processes = fields.Integer(
        string='Nº of processes',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help="Total number of processes",
        compute=lambda self: self._compute_total_of_processes()
    )

    approval = fields.Date(
        string='Approval date',
        required=False,
        readonly=False,
        index=False,
        default=fields.Date.today(),
        help='Choose the approval date',
        track_visibility='onchange',
    )


    @api.depends('tendering_process_ids')
    def _compute_total_of_vacancies(self):
        """ Returns computed value for total_of_vacancies field
        """
        for record in self:
            proc_ids = record.tendering_process_ids
            vacancy_ids = proc_ids.mapped('vacancy_position_ids')

            record.total_of_vacancies = sum(vacancy_ids.mapped('quantity'))


    @api.depends('tendering_process_ids')
    def _compute_total_of_processes(self):
        for record in self:
            record.total_of_processes = len(record.tendering_process_ids)


    def update_approval(self):
        for record in self:
            record.tendering_process_ids.set_approval(self.approval)

    def show_processes(self):
        """ Runs default view for tendering process with a filter to
        show only current offer items
        """

        act_wnd = self.env.ref('academy_public_tendering.'
                               'action_academy_public_tendering_act_window')

        if act_wnd.domain:
            if isinstance(act_wnd.domain, str):
                domain = safe_eval(act_wnd.domain)
            else:
                domain = act_wnd.domain
        else:
            domain = []

        ids = self.tendering_process_ids.mapped('id')
        domain.append(('id', 'in', ids))

        values = {
            'type': act_wnd['type'],
            'name': act_wnd['name'],
            'res_model': act_wnd['res_model'],
            'view_mode': act_wnd['view_mode'],
            'target': act_wnd['target'],
            'domain': domain,
            'context': self.env.context,
            'limit': act_wnd['limit'],
            'help': act_wnd['help'],
            'view_ids': act_wnd['view_ids'],
            'views': act_wnd['views']
        }

        if act_wnd.search_view_id:
            values['search_view_id'] = act_wnd['search_view_id'].id

        return values
