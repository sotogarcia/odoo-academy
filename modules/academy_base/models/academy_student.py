# -*- coding: utf-8 -*-
""" AcademyStudent

This module contains the academy.student Odoo model which stores
all student attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
from odoo.osv.expression import OR
from odoo.osv.expression import AND, FALSE_DOMAIN

from logging import getLogger

_logger = getLogger(__name__)


class AcademyStudent(models.Model):
    """ A student is a partner who can be enrolled on training actions
    """

    _name = 'academy.student'
    _description = u'Academy student'

    _inherit = ['mail.thread']
    _inherits = {'res.partner': 'res_partner_id'}

    res_partner_id = fields.Many2one(
        string='Partner',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='res.partner',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    enrolment_ids = fields.One2many(
        string='Student enrolments',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.action.enrolment',
        inverse_name='student_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    enrolment_count = fields.Integer(
        string='Nº enrolments',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of enrolments',
        compute='_compute_enrolment_count'
    )

    training_action_ids = fields.Many2manyView(
        string='Training actions',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Show training actions in which this student has been enrolled',
        comodel_name='academy.training.action',
        relation='academy_training_action_student_rel',
        column1='student_id',
        column2='training_action_id',
        domain=[],
        context={},
        limit=None,
        copy=False
    )

    @api.depends('enrolment_ids')
    def _compute_enrolment_count(self):
        for record in self:
            record.enrolment_count = len(record.enrolment_ids)

    @api.onchange('enrolment_ids')
    def _onchange_enrolment_ids(self):
        self.enrolment_count = len(self.enrolment_ids)

    attainment_id = fields.Many2one(
        string='Educational attainment',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Choose related educational attainment',
        comodel_name='academy.educational.attainment',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    birthday = fields.Date(
        string='Birthday',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Date on which the student was born'
    )

    _sql_constraints = [
        (
            'unique_partner',
            'UNIQUE(res_partner_id)',
            _(u'There is already a student for this contact')
        )
    ]

    @api.constrains('res_partner_id')
    def _check_res_partner_id(self):
        partner_obj = self.env['res.partner']
        msg = _('There is already a student with that VAT number or email')

        for record in self:
            if record.res_partner_id:
                leafs = [FALSE_DOMAIN]

                if record.vat:
                    leafs.append([('vat', '=ilike', record.vat)])

                if record.email:
                    leafs.append([('email', '=ilike', record.email)])

                if partner_obj.search_count(OR(leafs)) > 1:
                    raise ValidationError(msg)

    @api.model
    def default_get(self, fields):
        parent = super(AcademyStudent, self)
        values = parent. default_get(fields)

        values['employee'] = False
        values['type'] = 'contact'
        values['is_company'] = False

        return values

    @staticmethod
    def _eval_domain(domain):
        """ Evaluate a domain expresion (str, False, None, list or tuple) an
        returns a valid domain

        Arguments:
            domain {mixed} -- domain expresion

        Returns:
            mixed -- Odoo valid domain. This will be a tuple or list
        """

        if domain in [False, None]:
            domain = []
        elif not isinstance(domain, (list, tuple)):
            try:
                domain = eval(domain)
            except Exception:
                domain = []

        return domain

    def edit_enrolments(self):

        self.ensure_one()

        act_xid = 'academy_base.action_training_action_enrolment_act_window'
        action = self.env.ref(act_xid)

        view_xid = ('academy_base.'
                    'view_academy_training_action_enrolment_edit_by_user_tree')

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.context))
        ctx.update({'default_student_id': self.id})
        ctx.update({'tree_view_ref': view_xid})

        domain = self._eval_domain(action.domain)
        domain = AND([domain, [('student_id', '=', self.id)]])

        action_values = {
            'name': _('Enrolments for «{}»').format(self.name),
            'type': action.type,
            'help': action.help,
            'domain': domain,
            'context': ctx,
            'res_model': action.res_model,
            'target': action.target,
            'view_mode': action.view_mode,
            'search_view_id': action.search_view_id.id,
            'target': 'current',
            'nodestroy': True
        }

        return action_values

    def go_to_contact(self):
        self.ensure_one()

        return {
            'name': self.res_partner_id.name,
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'res.partner',
            'res_id': self.res_partner_id.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'main',
        }
