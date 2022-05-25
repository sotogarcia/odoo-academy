# -*- coding: utf-8 -*-
""" AcademyTrainingAction

This module extends the academy.training.action Odoo model
"""

from odoo import models, fields

import odoo.addons.academy_base.models.utils.custom_model_fields as custom
from .utils.sql_m2m_through_view import ACADEMY_ACTION_AVAILABLE_TESTS

from odoo.exceptions import UserError
from odoo.tools.translate import _
from logging import getLogger

_logger = getLogger(__name__)


class AcademyTrainingAction(models.Model):
    """ Extends model adding a many2many field to link tests to actions
    """

    _inherit = 'academy.training.action'

    test_ids = fields.Many2many(
        string='Training action tests',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose the tests will be available in this training action',
        comodel_name='academy.tests.test',
        relation='academy_tests_test_training_action_rel',
        column1='training_action_id',
        column2='test_id',
        domain=[],
        context={},
        limit=None
    )

    available_test_ids = custom.Many2manyThroughView(
        string='Training action available tests',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose the tests will be available in this training activity',
        comodel_name='academy.tests.test',
        relation='academy_tests_test_available_in_training_action_rel',
        column1='training_action_id',
        column2='test_id',
        domain=[],
        context={},
        limit=None,
        sql=ACADEMY_ACTION_AVAILABLE_TESTS
    )

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
        test_ids = self.mapped('test_ids.id')

        if not test_ids:
            msg = _('There are no tests associated with this training '
                    'activity')
            raise UserError(msg)

        return {
            'model': 'ir.actions.act_window',
            'type': 'ir.actions.act_window',
            'name': _('Test attempts'),
            'res_model': 'academy.tests.attempt',
            'target': 'current',
            'view_mode': 'tree',
            'domain': [('test_id', 'in', test_ids)],
            'context': {}
        }
