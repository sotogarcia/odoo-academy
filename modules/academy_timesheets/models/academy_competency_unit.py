# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.osv.expression import TRUE_DOMAIN, FALSE_DOMAIN
from odoo.osv.expression import TERM_OPERATORS_NEGATION
from odoo.tools import safe_eval

from logging import getLogger


_logger = getLogger(__name__)


class AcademyCompetencyUnit(models.Model):
    """ Append fields to set teachers
    """

    _inherit = ['academy.competency.unit']

    session_ids = fields.One2many(
        string='Sessions',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='All sessions for competency unit',
        comodel_name='academy.training.session',
        inverse_name='competency_unit_id',
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
                acu."id" AS competency_unit_id,
                COUNT ( ats."id" ) :: INTEGER AS session_count
            FROM
                academy_competency_unit AS acu
            LEFT JOIN academy_training_session AS ats
                ON ats.competency_unit_id = acu."id" AND ats.active
            GROUP BY
                acu."id"
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
            record_ids = [item['competency_unit_id'] for item in results]
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
        compute='_compute_timesheet_fields',
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
                acu."id" AS competency_unit_id,
                COUNT ( ats."id" ) :: INTEGER AS session_count
            FROM
                academy_competency_unit AS acu
            LEFT JOIN academy_training_session AS ats
                ON ats.competency_unit_id = acu."id"
                AND ats.active AND ats."state" = 'draft'
            GROUP BY
                acu."id"
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
            record_ids = [item['competency_unit_id'] for item in results]
            domain = [('id', 'in', record_ids)]
        else:
            domain = FALSE_DOMAIN

        return domain

    def view_timesheets(self):
        action_xid = ('academy_timesheets.'
                      'action_academy_competency_unit_timesheet_act_window')
        action = self.env.ref(action_xid)

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.context))

        if self:
            domain = [('competency_unit_id', 'in', self.mapped('id'))]
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
