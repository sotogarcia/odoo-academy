# -*- coding: utf-8 -*-
""" AcademyCompetencyUnit

This module extends the academy.student Odoo model
"""

from odoo import models, fields
from odoo.tools.translate import _

import odoo.addons.academy_base.models.utils.custom_model_fields as custom
from .utils.sql_m2m_through_view import ACADEMY_STUDENT_AVAILABLE_TESTS

from logging import getLogger

_logger = getLogger(__name__)


class AcademyStudent(models.Model):
    """ Extend student adding available tests
    """

    _inherit = 'academy.student'

    available_test_ids = custom.Many2manyThroughView(
        string='Student available tests',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose the tests will be available to this student',
        comodel_name='academy.tests.test',
        relation='academy_tests_test_available_in_student_rel',
        column1='student_id',
        column2='test_id',
        domain=[],
        context={},
        limit=None,
        sql=ACADEMY_STUDENT_AVAILABLE_TESTS
    )

    question_statistics_ids = fields.One2many(
        string='Question statistics',
        required=False,
        readonly=True,
        index=False,
        default=None,
        comodel_name='academy.statistics.student.question.readonly',
        inverse_name='student_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None,
        help=('Show the statistics related with the questions answered by the '
              'student')
    )

    def show_test_attempts(self):
        self.ensure_one()

        form_xid = ('academy_tests.view_academy_tests_attempt_form')
        form_id = self.env.ref(form_xid).id

        tree_xid = ('academy_tests.view_academy_tests_attempt_tree')
        tree_id = self.env.ref(tree_xid).id

        print(form_id, tree_id)

        return {
            'name': _('Attempts of «{}»').format(self.name),
            'view_mode': 'tree,form',
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'view_type': 'form',
            'res_model': 'academy.tests.attempt',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id}
        }
