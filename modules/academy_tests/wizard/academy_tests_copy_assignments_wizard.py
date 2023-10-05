# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger
from odoo.exceptions import ValidationError

from odoo.addons.academy_base.models.academy_abstract_training_reference \
    import MAPPING_TRAINING_REFERENCES

_logger = getLogger(__name__)


class AcademyTestsCopyAssignmentsWizard(models.TransientModel):
    """ Allow to copy existing assignments to another training action.

    """

    _name = 'academy.tests.copy.assignments.wizard'
    _description = u'Academy tests copy assignments wizard'

    _rec_name = 'id'
    _order = 'id DESC'

    assignment_ids = fields.Many2many(
        string='Assignments',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_assignment_ids(),
        help='Chosen assignments',
        comodel_name='academy.tests.test.training.assignment',
        relation='academy_tests_copy_assignments_wizard_assignment_rel',
        column1='wizard_id',
        column2='assignment_id',
        domain=[],
        context={},
        limit=None
    )

    def default_assignment_ids(self):
        result_set = self.env['academy.tests.test.training.assignment']

        context = self.env.context
        active_model = context.get('active_model', False)

        if active_model == 'academy.tests.test.training.assignment':

            active_ids = context.get('active_ids', [])

            if not active_ids:
                active_id = context.get('active_id', None)
                if active_id:
                    active_ids = [active_id]

            if active_ids:
                domain = [('id', 'in', active_ids)]
                result_set = result_set.search(domain)

        return result_set

    training_ref = fields.Reference(
        string='Training',
        required=True,
        readonly=False,
        index=False,
        default=0,
        help='Target training object',
        selection=MAPPING_TRAINING_REFERENCES
    )

    training_activity_id = fields.Many2one(
        string='Training activity',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.activity',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        compute='_compute_training_activity_id'
    )

    @api.depends('training_ref')
    def _compute_training_activity_id(self):
        # activity_obj = self.env['academy.training.activity']
        # activity_type = type(activity_obj)

        for record in self:
            record.training_activity_id = None
            if record.has_training_action():
                record.training_activity_id = record.training_ref

    choose_actions = fields.Boolean(
        string='Choose actions',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help=('Check it to allow select target training actions instead the '
              'chosen training activity')
    )

    training_action_ids = fields.Many2many(
        string='Training actions',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.action',
        relation='academy_tests_copy_assignments_wizard_training_action_rel',
        column1='wizard_id',
        column2='training_action_id',
        domain=[],
        context={},
        limit=None
    )

    state = fields.Selection(
        string='State',
        required=True,
        readonly=True,
        index=False,
        default='step1',
        help='Wizard steps',
        selection=[('step1', 'Source'), ('step2', 'Destination')]
    )

    @staticmethod
    def _real_id(record_set, single=False):
        """ Return a list with no NewId's of a single no NewId
        """

        result = []

        if record_set and single:
            record_set.ensure_one()

        for record in record_set:
            if isinstance(record.id, models.NewId):
                result.append(record._origin.id)
            else:
                result.append(record.id)

        if single:
            result = result[0] if len(result) == 1 else None

        return result

    @api.constrains('assignment_ids')
    def _check_assignment_ids(self):
        message = _('No assignments have been chosen to copy')

        for record in self:
            if not record.assignment_ids:
                raise ValidationError(message)

    @api.constrains('training_ref')
    def _check_training_ref(self):
        message = _('A target training object has not been chosen')

        for record in self:
            if not record.training_ref:
                raise ValidationError(message)

    @api.constrains('training_action_ids')
    def _check_training_action_ids(self):
        message = _('No training actions have been chosen as targets')
        # activity_obj = self.env['academy.training.activity']
        # activity_type = type(activity_obj)

        for record in self:
            if not record.has_training_action():
                continue

            if not record.choose_actions:
                continue

            if not record.training_action_ids:
                raise ValidationError(message)

    def has_training_action(self):
        self.ensure_one()

        activity_obj = self.env['academy.training.activity']
        activity_type = type(activity_obj)

        return isinstance(self.training_ref, activity_type)

    @api.model
    def _compute_reference(self, training):
        training.ensure_one()

        for pair in MAPPING_TRAINING_REFERENCES:
            model = pair[0]
            model_obj = self.env[model]
            model_type = type(model_obj)

            if isinstance(training, model_type):
                return '{},{}'.format(model, training.id)

    @api.model
    def _assignment_exists(self, test_id, training_ref):
        assignment_obj = self.env['academy.tests.test.training.assignment']

        if isinstance(training_ref, models.Model):
            training_ref = self._compute_reference(training_ref)

        if isinstance(test_id, models.Model):
            test_id = test_id.id

        domain = [
            ('test_id', '=', test_id),
            ('training_ref', '=', training_ref)
        ]

        return assignment_obj.search_count(domain) > 0

    def perform_action(self):
        self.ensure_one()

        msg = _('The assignment of Test «{}» to training «{}» already exists.')

        assignment_obj = self.env['academy.tests.test.training.assignment']
        current_user = self.env.user

        if self.has_training_action() and self.choose_actions:
            training_set = self.training_action_ids
        else:
            training_set = self.training_ref

        for training in training_set:
            training_ref = self._compute_reference(training)

            for assignment in self.assignment_ids:
                test_id = assignment.test_id.id

                if self._assignment_exists(test_id, training_ref):
                    _logger.warning(msg.format(test_id, training_ref))
                    continue

                values = {
                    'name': assignment.name,
                    'active': assignment.active,
                    'test_id': test_id,
                    'training_ref': training_ref,
                    'release': assignment.release,
                    'expiration': assignment.expiration,
                    'secondary_id': assignment.secondary_id.id,
                    'correction_scale_id': assignment.correction_scale_id.id,
                    'lock_time': assignment.lock_time,
                    'time_by': assignment.time_by,
                    'validate_test': assignment.validate_test,
                    'random_template_id': assignment.random_template_id.id,
                    'owner_id': current_user.id,
                    'subrogate_id': None,
                }

                assignment_obj.create(values)
