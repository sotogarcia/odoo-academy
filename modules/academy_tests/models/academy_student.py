# -*- coding: utf-8 -*-
""" AcademyCompetencyUnit

This module extends the academy.student Odoo model
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.osv.expression import FALSE_DOMAIN
from .utils.sql_inverse_searches import SEARCH_STUDENT_ATTEMPT_COUNT

from logging import getLogger

_logger = getLogger(__name__)


class AcademyStudent(models.Model):
    """ Extend student adding available tests
    """

    _inherit = 'academy.student'

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
        store=False,
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

    assignment_count = fields.Integer(
        string='Nº assignments',
        required=False,
        readonly=True,
        index=False,
        default=0,
        store=False,
        help='Show the number or test assignments for this training',
        compute='_compute_assignment_count'
    )

    def _compute_assignment_count(self):
        assignment_obj = self.env['academy.tests.test.training.assignment']

        for record in self:
            domain = [('student_ids', '=', record.id)]
            result = assignment_obj.search_count(domain)
            record.assignment_count = result

    def view_test_attempts(self):
        self.ensure_one()

        return {
            'name': _('Attempts of «{}»').format(self.name),
            'view_mode': 'tree,pivot,form',
            'view_mode': 'pivot,tree,form,graph',
            'res_model': 'academy.tests.attempt',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': [('student_id', '=', self.id)]
        }

    def view_test_assignments(self):
        self.ensure_one()

        path = 'enrolment_ids.available_assignment_ids.id'
        assignment_ids = self.mapped(path)

        return {
            'model': 'ir.actions.act_window',
            'type': 'ir.actions.act_window',
            'name': _('Test assignments'),
            'res_model': 'academy.tests.test.training.assignment',
            'target': 'current',
            'view_mode': 'kanban,tree,form',
            'domain': [('id', 'in', assignment_ids)],
            'context': {
                'name_get': 'training',
                'search_default_my_assignments': 1,
                'create': False
            },
        }
