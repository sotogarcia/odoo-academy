# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.addons.academy_base.utils.record_utils import get_active_records
from logging import getLogger


_logger = getLogger(__name__)


class AcademyTestsAttemptWizard(models.TransientModel):
    """ Wizard to perform massive changes over test attempts.
    """

    _name = 'academy.tests.attempt.wizard'
    _description = u'Academy tests attempt wizard'

    _rec_name = 'id'
    _order = 'id DESC'

    attempt_ids = fields.Many2many(
        string='Attempt',
        required=False,
        readonly=True,
        index=False,
        default=lambda self: self.default_attempt_ids(),
        help='Chosen test attempts',
        comodel_name='academy.tests.attempt',
        relation='academy_tests_attempt_wizard_attempt_rel',
        column1='wizard_id',
        column2='attempt_id',
        domain=[],
        context={},
        limit=None
    )

    def default_attempt_ids(self):
        return get_active_records(self.env, 'academy.tests.attempt')

    attempt_count = fields.Integer(
        string='Attempt count',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help='Total number of chosen test attempts',
        compute='_compute_attempt_count'
    )

    @api.depends('attempt_ids')
    def _compute_attempt_count(self):
        for record in self:
            record.attempt_count = len(record.attempt_ids)

    wizard_action = fields.Selection(
        string='Action',
        required=True,
        readonly=False,
        index=False,
        default=False,
        help='Action will be performed over selected records',
        selection=[
            ('close', 'Close'),
            ('recalculate', 'Recalculate'),
            ('prevalence', 'Update user rank'),
            ('rank', 'Update assignment rank'),
            ('both_ranks', 'Update both ranks')
        ]
    )

    def _perform_action(self):
        self.ensure_one()

        target_set = self.attempt_ids

        if self.wizard_action == 'close':
            opened_set = target_set.filtered(lambda r: not r.closed)
            opened_set.close()
        elif self.wizard_action == 'recalculate':
            target_set.recalculate()
        elif self.wizard_action == 'prevalence':
            individual_ids = target_set.mapped('individual_id').ids
            target_set.update_prevalence(individual_ids)
        elif self.wizard_action == 'rank':
            assignment_ids = target_set.mapped('assignment_id').ids
            target_set.update_rank(assignment_ids)
        elif self.wizard_action == 'both_ranks':
            individual_ids = target_set.mapped('individual_id').ids
            target_set.update_prevalence(individual_ids)
            assignment_ids = target_set.mapped('assignment_id').ids
            target_set.update_rank(assignment_ids)

    def perform_action(self):
        for record in self:
            record._perform_action()
