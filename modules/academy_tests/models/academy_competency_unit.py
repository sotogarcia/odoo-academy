# -*- coding: utf-8 -*-
""" AcademyCompetencyUnit

This module extends the academy.competency.unit Odoo model
"""

from odoo import models, fields, api
from logging import getLogger

_logger = getLogger(__name__)


class AcademyCompetencyUnit(models.Model):
    """ Extends model adding two many2many fields to link tests and units
    """

    _inherit = 'academy.competency.unit'

    number_of_questions = fields.Integer(
        string='Number of questions',
        required=True,
        readonly=False,
        index=False,
        default=2,
        help='Number of questions will be added in templates'
    )

    assignment_ids = fields.One2many(
        string='Test assignments',
        required=False,
        readonly=False,
        index=True,
        default=None,
        comodel_name='academy.tests.test.training.assignment',
        inverse_name='competency_unit_id',
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
        inverse_name='competency_unit_id',
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

    test_block_id = fields.Many2one(
        string='Test block',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Test block will be added to questions in templates',
        comodel_name='academy.tests.test.block',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    questions_ratio = fields.Char(
        string='Req/Av',
        required=False,
        readonly=True,
        index=False,
        default=None,
        size=15,
        translate=False,
        store=False,
        compute='_compute_questions_ratio',
        help=('Number of required questions to create a default test and the '
              'total number of related questions available in database')
    )

    @api.depends('number_of_questions', 'available_question_count')
    def _compute_questions_ratio(self):
        for record in self:
            req = record.number_of_questions
            av = record.available_question_count
            record.questions_ratio = '{} / {}'.format(req, av)

    def create_test_template(self, no_open=False):
        template_obj = self.env['academy.tests.random.template']
        module_obj = self.env['academy.training.module']

        values = module_obj.get_template_values(self)

        template = template_obj.create(values)

        if not no_open and template:
            return module_obj._template_act_window(template)

    def check_competency_unit(self):
        xid = 'academy_tests.mail_template_check_competency_unit'
        mail_template = self.env.ref(xid)

        for record in self:
            mail_template.send_mail(record.id)
