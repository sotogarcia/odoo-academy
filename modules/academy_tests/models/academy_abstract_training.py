# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.osv.expression import OR

from logging import getLogger


_logger = getLogger(__name__)


class AcademyAbstractTraining(models.AbstractModel):
    """ Comment fields and methods will be used in all training items
    Training enrolment, action, activity, competency, module
    """

    _inherit = ['academy.abstract.training']

    random_template_id = fields.Many2one(
        string='Default template',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose a test template will be used as default',
        comodel_name='academy.tests.random.template',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    available_assignment_ids = fields.Many2many(
        string='Available assignments',
        required=False,
        readonly=True,
        index=False,
        default=None,
        comodel_name='academy.tests.test.training.assignment',
        relation='academy_abstract_training_assignment_rel',
        column1='training_id',
        column2='assignment_id',
        domain=[],
        context={},
        limit=None,
        store=False,
        compute='_compute_available_assignment_ids',
        help='List all available test assignments for the training module'
    )

    @api.depends('assignment_ids')
    def _compute_available_assignment_ids(self):
        for record in self:
            assignment_set = record.get_available('assignment_ids')

            if assignment_set:
                assignment_ids = assignment_set.mapped('id')
                record.available_assignment_ids = [(6, 0, assignment_ids)]
            else:
                record.available_assignment_ids = [(5, 0, 0)]

    available_assignment_count = fields.Integer(
        string='Nº available assignments',
        required=False,
        readonly=True,
        index=False,
        default=0,
        store=False,
        compute='_compute_available_assignment_count',
        help=('Show the number of test assignments that have been created for'
              'this training action')
    )

    @api.depends('assignment_ids')
    def _compute_available_assignment_count(self):
        for record in self:
            assignment_set = record.get_available('assignment_ids')
            record.available_assignment_count = len(assignment_set)

    available_template_count = fields.Integer(
        string='Nº available templates',
        required=False,
        readonly=True,
        index=False,
        default=0,
        store=False,
        compute='_compute_available_template_count',
        help=('Show the number of test templates available to be used in this '
              'training action')
    )

    @api.depends('template_ids')
    def _compute_available_template_count(self):
        for record in self:
            template_set = record.get_available('template_ids')
            record.available_template_count = len(template_set)

    available_question_ids = fields.Many2many(
        string='Questions',
        required=False,
        readonly=True,
        index=False,
        default=None,
        comodel_name='academy.tests.question',
        relation='academy_abstract_training_question_rel',
        column1='training_id',
        column2='question_id',
        domain=[],
        context={},
        limit=None,
        store=False,
        compute='_compute_available_question_ids',
        help='List all questions that match the chosen topics and categories'
    )

    def _compute_available_question_ids(self):
        for record in self:
            path = self.get_path_down()

            path = '.'.join([path, 'topic_link_ids.question_ids.id'])

            question_ids = record.mapped(path)
            if question_ids:
                record.available_question_ids = [(6, 0, question_ids)]
            else:
                record.available_question_ids = [(5, 0, 0)]

    available_question_count = fields.Integer(
        string='Nº questions',
        required=True,
        readonly=True,
        index=False,
        default=0,
        store=False,
        help='Show the number of related questions',
        compute='_compute_available_question_count'
    )

    def _compute_available_question_count(self):
        for record in self:
            record.available_question_count = \
                len(record.available_question_ids)

    def _compute_view_test_assignments_domain(self):
        """Allows to child models to override domain
        """

        self.ensure_one()

        inverse_name = self.get_inverse_field_name()
        domain = [(inverse_name, '=', self.id)]

        assignment_set = self.get_available('assignment_ids')
        if assignment_set:
            assignment_ids = assignment_set.mapped('id')
            domain = OR([domain, [('id', 'in', assignment_ids)]])

        return domain

    def view_test_assignments(self):
        self.ensure_one()

        domain = self._compute_view_test_assignments_domain()

        return {
            'model': 'ir.actions.act_window',
            'type': 'ir.actions.act_window',
            'name': _('Test assignments'),
            'res_model': 'academy.tests.test.training.assignment',
            'target': 'current',
            'view_mode': 'kanban,tree,form',
            'domain': domain,
            'context': {
                'name_get': 'test',
                'default_training_ref': '{},{}'.format(self._name, self.id),
                'search_default_my_assignments': 1
            }
        }

    def view_test_templates(self):
        self.ensure_one()

        inverse_name = self.get_inverse_field_name()
        domain = [(inverse_name, '=', self.id)]

        template_set = self.get_available('template_ids')
        if template_set:
            template_ids = template_set.mapped('id')
            domain = OR([domain, [('id', 'in', template_ids)]])

        return {
            'model': 'ir.actions.act_window',
            'type': 'ir.actions.act_window',
            'name': _('Test templates'),
            'res_model': 'academy.tests.random.template',
            'target': 'current',
            'view_mode': 'kanban,tree,form',
            'domain': domain,
            'context': {
                'name_get': 'test',
                'default_training_ref': '{},{}'.format(self._name, self.id),
                'search_default_my_templates': 1
            }
        }

    def view_available_questions(self):
        self_name = self.get_name()
        view_name = _('Questions in {}').format(self_name)

        question_id = self.available_question_ids.mapped('id')

        return {
            'model': 'ir.actions.act_window',
            'type': 'ir.actions.act_window',
            'name': view_name,
            'res_model': 'academy.tests.random.template',
            'target': 'current',
            'view_mode': 'kanban,tree,form',
            'domain': [('id', 'in', question_id)],
            'context': {
                'name_get': 'test',
                'search_default_my_questions': 1
            }
        }

    def new_assignment_to_test(self):
        self.ensure_one()

        return {
            'model': 'ir.actions.act_window',
            'type': 'ir.actions.act_window',
            'name': _('New assignment'),
            'res_model': 'academy.tests.test.training.assignment',
            'target': 'new',
            'view_mode': 'form',
            'context': {
                'default_training_ref': '{},{}'.format(self._name, self.id)
            }
        }

    def check_training_module(self):
        xid = 'academy_tests.mail_template_check_training_module'
        mail_template = self.env.ref(xid)

        for record in self:
            mail_template.send_mail(record.id)
