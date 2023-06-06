# -*- coding: utf-8 -*-
""" AcademyTrainingActionEnrolment

This module extends the academy.training.action.enrolment Odoo model
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger

_logger = getLogger(__name__)


class AcademyTrainingActionEnrolment(models.Model):
    """ Extends model adding a many2many field to link tests to actions
    """

    _inherit = 'academy.training.action.enrolment'

    assignment_ids = fields.One2many(
        string='Test assignments',
        required=False,
        readonly=False,
        index=True,
        default=None,
        comodel_name='academy.tests.test.training.assignment',
        inverse_name='enrolment_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None,
        help=('List of test assignments that have been created for this '
              'training action enrollment')
    )

    assignment_count = fields.Integer(
        string='Nº assignments',
        required=False,
        readonly=True,
        index=False,
        default=0,
        store=False,
        compute='_compute_assignment_count',
        help=('Show the number of test assignments that have been created for'
              'this training action enrollment')
    )

    @api.depends('assignment_ids')
    def _compute_assignment_count(self):
        for record in self:
            record.assignment_count = \
                len(record.assignment_ids)

    template_ids = fields.One2many(
        string='Templates',
        required=False,
        readonly=False,
        index=True,
        default=None,
        comodel_name='academy.tests.random.template',
        inverse_name='enrolment_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None,
        help=('List of test templates available to be used in this training '
              'action enrollment')
    )

    template_count = fields.Integer(
        string='Nº templates',
        required=False,
        readonly=True,
        index=False,
        default=0,
        store=False,
        compute='_compute_template_count',
        help=('Show the number of test templates available to be used in this '
              'training action enrollment')
    )

    @api.depends('template_ids')
    def _compute_template_count(self):
        for record in self:
            record.template_count = len(record.template_ids)

    available_assignment_ids = fields.Many2manyView(
        string='Available assignments',
        required=False,
        readonly=True,
        index=False,
        default=None,
        comodel_name='academy.tests.test.training.assignment',
        relation='academy_training_action_enrolment_available_assignment_rel',
        column1='enrolment_id',
        column2='related_id',
        domain=[],
        context={},
        limit=None,
        store=True,
        help='List all available test assignments in this enrolment',
        copy=False
    )

    available_assignment_count = fields.Integer(
        string='Nº available assignments',
        required=False,
        readonly=True,
        index=False,
        default=0,
        store=False,
        compute='_compute_available_assignment_count',
        help=('Show the number of test assignments that have been created for'
              'this enrolment')
    )

    @api.depends('assignment_ids')
    def _compute_available_assignment_count(self):
        for record in self:
            assignment_set = record.available_assignment_ids
            record.available_assignment_count = len(assignment_set)

    def _compute_view_test_assignments_domain(self):
        assignment_ids = self.mapped('available_assignment_ids.id')
        return [('id', 'in', assignment_ids)]

    attempt_count = fields.Integer(
        string='Attempt count',
        readonly=True,
        related="student_id.attempt_count"
    )

    def view_test_attempts(self):
        self.ensure_one()

        irf = self.env.ref('academy_tests.ir_filter_student_attempts')

        return {
            'name': _('Attempts of «{}»').format(self.display_name),
            'view_mode': 'tree,pivot,form',
            'view_mode': 'pivot,tree,form,graph',
            'res_model': 'academy.tests.attempt.resume.helper',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': [('student_id', '=', self.student_id.id)],
            'context': irf.context
        }

    # def view_test_assignments(self):
    #     self.ensure_one()

    #     path = 'available_assignment_ids.id'
    #     assignment_ids = self.mapped(path)

    #     return {
    #         'model': 'ir.actions.act_window',
    #         'type': 'ir.actions.act_window',
    #         'name': _('Test assignments'),
    #         'res_model': 'academy.tests.test.training.assignment',
    #         'target': 'current',
    #         'view_mode': 'kanban,tree,form',
    #         'domain': [('id', 'in', assignment_ids)],
    #         'context': {
    #             'name_get': 'training',
    #             'search_default_my_assignments': 1,
    #             'create': False
    #         },
    #     }
