# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class AcademyTestsManualCategorizationProject(models.Model):
    """ Manual categorization project
    """

    _name = 'academy.tests.manual.categorization.project'
    _description = u'academy.tests.manual.categorization.project'

    _rec_name = 'name'
    _order = 'write_date DESC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Name for this level',
        size=255,
        translate=True
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this level',
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help=('If the active field is set to false, it will allow you to '
              'hide record without removing it')
    )

    question_ids = fields.Many2many(
        string='Questions',
        required=False,
        readonly=False,
        index=True,
        default=lambda self: self.default_question_ids(),
        help='Choose questions will be categorized',
        comodel_name='academy.tests.question',
        relation='academy_tests_manual_categorization_project_question_rel',
        column1='project_id',
        column2='question_id',
        domain=[],
        context={},
        limit=None
    )

    question_id = fields.Many2one(
        string='Question',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Choosen question',
        comodel_name='academy.tests.question',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    def default_question_ids(self):
        question_set = self.env['academy.tests.question']

        active_model = self.env.context.get('active_model', None)
        active_id = self.env.context.get('active_id', -1)
        active_ids = self.env.context.get('active_ids', [active_id])

        if active_ids[0] >= 1:

            domain = [('id', 'in', active_ids)]
            record_set = self.env[active_model].search(domain)

            if active_model == 'academy.tests.test':
                question_set = record_set.mapped('question_ids.question_id')

            elif active_model == 'academy.tests.test.question.rel':
                question_set = record_set.mapped('question_id')

            elif active_model == 'academy.tests.question':
                question_set = record_set

        return question_set.search([('id', '>', 0)], limit=10)
