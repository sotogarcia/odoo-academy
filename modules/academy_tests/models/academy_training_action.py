# -*- coding: utf-8 -*-
""" AcademyTrainingAction

This module extends the academy.training.action Odoo model
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger

_logger = getLogger(__name__)


class AcademyTrainingAction(models.Model):
    """ Extends model adding a many2many field to link tests to actions
    """

    _inherit = 'academy.training.action'

    assignment_ids = fields.One2many(
        string='Test assignments',
        required=False,
        readonly=False,
        index=True,
        default=None,
        comodel_name='academy.tests.test.training.assignment',
        inverse_name='training_action_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None,
        help=('List of test assignments that have been created for this '
              'training action')
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
              'this training action')
    )

    @api.depends('assignment_ids')
    def _compute_assignment_count(self):
        for record in self:
            record.assignment_count = \
                len(record.assignment_ids)

    attempt_count = fields.Integer(
        string='Attempt count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of test attempts',
        store=False,
        compute='_compute_attempt_count'
    )

    @api.depends('assignment_ids')
    def _compute_attempt_count(self):
        for record in self:
            summands = self.mapped('assignment_ids.attempt_count')
            record.attempt_count = sum(summands)

    template_ids = fields.One2many(
        string='Templates',
        required=False,
        readonly=False,
        index=True,
        default=None,
        comodel_name='academy.tests.random.template',
        inverse_name='training_action_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None,
        help=('List of test templates available to be used in this training '
              'action')
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
              'training action')
    )

    @api.depends('template_ids')
    def _compute_template_count(self):
        for record in self:
            record.template_count = len(record.template_ids)

    def create_test_template(self, no_open=False):
        template_obj = self.env['academy.tests.random.template']
        module_obj = self.env['academy.training.module']

        values = module_obj.get_template_values(
            self.competency_unit_ids, name=self.action_name, context=self)

        template = template_obj.create(values)

        if not no_open and template:
            return module_obj._template_act_window(template)

    def view_test_attempts(self):
        self.ensure_one()

        assignment_ids = self.mapped('assignment_ids.id')
        irf = self.env.ref('academy_tests.ir_filter_assignment_attempts')

        return {
            'name': _('Attempts of «{}»').format(self.name),
            'view_mode': 'tree,pivot,form',
            'view_mode': 'pivot,tree,form,graph',
            'res_model': 'academy.tests.attempt.resume.helper',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': [('assignment_id', 'in', assignment_ids)],
            'context': irf.context
        }
