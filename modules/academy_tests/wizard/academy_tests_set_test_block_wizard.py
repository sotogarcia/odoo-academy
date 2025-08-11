# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.addons.academy_base.utils.record_utils import get_active_records
from odoo.exceptions import ValidationError

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTestsSetTestBlockWizard(models.TransientModel):

    _name = 'academy.tests.set.test.block.wizard'
    _description = u'Academy tests set test block wizard'

    _rec_name = 'id'
    _order = 'id DESC'


    question_rel_ids = fields.Many2many(
        string='Target links',
        required=False,
        readonly=True,
        index=False,
        default=lambda self: self._default_question_rel_ids(),
        help=False,
        comodel_name='academy.tests.test.question.rel',
        relation='academy_tests_set_test_block_wizard_link_rel',
        column1='wizard_id',
        column2='link_id',
        domain=[],
        context={},
        limit=None
    )

    def _default_question_rel_ids(self):
        return get_active_records(self.env, 'academy.tests.test.question.rel')

    assign_to_block_id = fields.Many2one(
        string='Assign to block',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Target block for unassigned questions, if applicable',
        comodel_name='academy.tests.test.block',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    sort_after = fields.Boolean(
        string='Sort after',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help=False
    )

    def perform_action(self):
        for record in self:
            if not record.question_rel_ids:
                continue
            record._perform_action()

    def _perform_action(self):
        self.ensure_one()

        test_set = self.mapped('question_rel_ids.test_id')
        if len(test_set) > 1:
            err = _('There are questions from more than one test.')
            raise ValidationError(err)

        values = {'test_block_id': self.assign_to_block_id.id}
        self.question_rel_ids.write(values)

        if self.sort_after:
            wizard_obj = self.env['academy.tests.test.question.shuffle.wizard']
            wizard = wizard_obj.create_from_recordset(test_set)
            wizard.shuffle_scope = 'questions'
            wizard.unassigned_question_handling = 'beginning'
            wizard.perform_action()
