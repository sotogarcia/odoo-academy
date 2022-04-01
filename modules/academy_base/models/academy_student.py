# -*- coding: utf-8 -*-
""" AcademyStudent

This module contains the academy.student Odoo model which stores
all student attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from .utils.custom_model_fields import Many2manyThroughView

from logging import getLogger

_logger = getLogger(__name__)


class AcademyStudent(models.Model):
    """ A student is a partner who can be enroled on training actions
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

    training_action_ids = Many2manyThroughView(
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
        # sql=must be empty. View will be created in training.action
    )

    @api.depends('enrolment_ids')
    def _compute_enrolment_count(self):
        for record in self:
            record.enrolment_count = len(record.enrolment_ids)

    @api.onchange('enrolment_ids')
    def _onchange_enrolment_ids(self):
        self.enrolment_count = len(self.enrolment_ids)

    def edit_enrolments(self):
        self.ensure_one()

        view_xid = ('academy_base.'
                    'view_academy_training_action_enrolment_edit_by_user_tree')
        return {
            'name': _('Enrolments for «{}»').format(self.name),
            'view_mode': 'tree',
            'view_id': self.env.ref(view_xid).id,
            'view_type': 'form',
            'res_model': 'academy.training.action.enrolment',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': [('student_id', '=', self.id)],
        }
