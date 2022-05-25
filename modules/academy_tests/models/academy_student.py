# -*- coding: utf-8 -*-
""" AcademyCompetencyUnit

This module extends the academy.student Odoo model
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.osv.expression import FALSE_DOMAIN
from .utils.sql_inverse_searches import SEARCH_STUDENT_ATTEMPT_COUNT
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

    attempt_ids = fields.One2many(
        string='Attempts',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Related test attempts',
        comodel_name='academy.tests.attempt',
        inverse_name='student_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    attempt_count = fields.Integer(
        string='Attempt count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of test attempts',
        compute='_compute_attempt_count',
        search='_search_attempt_count'
    )

    @api.depends('attempt_ids')
    def _compute_attempt_count(self):
        for record in self:
            record.attempt_count = len(record.attempt_ids)

    def _search_attempt_count(self, operator, value):
        domain = FALSE_DOMAIN
        operator, value = self._ensure_search_attempt_count_(operator, value)
        query = SEARCH_STUDENT_ATTEMPT_COUNT.format(operator, value)

        self.env.cr.execute(query)
        rows = self.env.cr.dictfetchall()

        if rows:
            student_ids = [row['student_id'] for row in rows]
            domain = [('id', 'in', student_ids)]

        return domain

    def view_test_attempts(self):
        self.ensure_one()

        form_xid = 'academy_tests.view_academy_tests_attempt_form'
        form_id = self.env.ref(form_xid).id

        tree_xid = 'academy_tests.view_academy_tests_attempt_student_tree'
        tree_id = self.env.ref(tree_xid).id

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
