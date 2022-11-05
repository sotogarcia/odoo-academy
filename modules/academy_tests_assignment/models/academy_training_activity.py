# -*- coding: utf-8 -*-
""" AcademyTrainingActivity

This module extends the academy.training.activity Odoo model
"""

from odoo import models, fields, api
from odoo.tools.translate import _

from logging import getLogger

_logger = getLogger(__name__)


class AcademyTrainingActivity(models.Model):
    """ Extends model adding a many2many field to link tests to actions
    """

    _inherit = 'academy.training.activity'

    available_time = fields.Float(
        string='Default time',
        required=False,
        readonly=False,
        index=False,
        default=0.5,
        digits=(16, 2),
        help=('Default available time to complete exercises. This value will '
              'be used to create new templates')
    )

    correction_scale_id = fields.Many2one(
        string='Default correction scale',
        required=False,
        readonly=False,
        index=False,
        default=None,
        comodel_name='academy.tests.correction.scale',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        help=('Choose the default correction scale will be used on the new ',
              'created templates')
    )

    template_ids = fields.One2many(
        string='Templates',
        required=False,
        readonly=False,
        index=True,
        default=None,
        comodel_name='academy.tests.random.template',
        inverse_name='training_activity_id',
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

    available_question_ids = fields.Many2manyView(
        string='Available questions',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Show questions available in the module',
        comodel_name='academy.tests.question',
        relation='academy_tests_question_training_activity_rel',
        column1='training_activity_id',
        column2='question_id',
        domain=[],
        context={},
        limit=None
    )

    def create_test_template(self, no_open=False):
        template_obj = self.env['academy.tests.random.template']
        module_obj = self.env['academy.training.module']

        values = module_obj.get_template_values(
            self.competency_unit_ids, name=self.name)

        template = template_obj.create(values)

        if not no_open and template:
            return module_obj._template_act_window(template)

    def view_test_templates(self):
        pass

    random_template_id = fields.Many2one(
        string='Random template',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.random.template',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )
