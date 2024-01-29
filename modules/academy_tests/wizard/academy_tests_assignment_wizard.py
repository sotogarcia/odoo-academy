# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError
from odoo.tools import safe_eval
from odoo.addons.academy_base.utils.datetime_utils import localized_dt, get_tz
from odoo.addons.academy_base.utils.record_utils import get_active_records

from logging import getLogger
from dateutil.relativedelta import relativedelta

_logger = getLogger(__name__)


class AcademyTestsAssignmentWizard(models.TransientModel):
    """ Allow to assign multiple tests to multiple actions
    """

    _name = 'academy.tests.assignment.wizard'
    _description = u'Wizard to assign multiple tests to multiple actions'

    _inherit = ['ownership.mixin']

    _rec_name = 'id'
    _order = 'id DESC'

    state = fields.Selection(
        string='Step',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_state(),
        help='Current wizard step',
        selection=lambda self: self.selection_state()
    )

    def default_state(self):
        active_model = self.env.context.get('active_model', False)
        return 'sa' if active_model == 'academy.training.action' else 'st'

    def selection_state(self):
        steps = [('st', _('Exercises')), ('so', _('Options'))]
        step_action = ('sa', _('Training'))

        active_model = self.env.context.get('active_model', False)
        position = 0 if active_model == 'academy.training.action' else 1
        steps.insert(position, step_action)

        return steps

    test_ids = fields.Many2many(
        string='Tests',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_test_ids(),
        help='Choose the test will be assigned',
        comodel_name='academy.tests.test',
        relation='academy_tests_assignment_wizard_test_rel',
        column1='wizard_id',
        column2='test_id',
        domain=[],
        context={},
        limit=None
    )

    def default_test_ids(self):
        return get_active_records(self.env, 'academy.tests.test')

    training_action_ids = fields.Many2many(
        string='Training actions',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_training_action_ids(),
        help=('Choose the training actions to which the chosen test will be '
              'assigned'),
        comodel_name='academy.training.action',
        relation='academy_tests_assignment_wizard_training_action_rel',
        column1='wizard_id',
        column2='training_action_id',
        domain=[],
        context={},
        limit=None
    )

    def default_training_action_ids(self):
        return get_active_records(self.env, 'academy.training.action')

    release = fields.Datetime(
        string='Release',
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self.default_release(),
        help='Date and time from which the test will be available'
    )

    def default_release(self):
        return fields.datetime.now()

    expiration = fields.Datetime(
        string='Expiration',
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self.default_expiration(),
        help='Date and time from which the test will be available'
    )

    def default_expiration(self):
        return self.default_release() + relativedelta(years=100)

    use_options = fields.Selection(
        string='Use options',
        required=True,
        readonly=False,
        index=False,
        default='atw',
        help=False,
        selection=[
            ('aw', 'Action, Wizard'),
            ('tw', 'Test, Wizard'),
            ('atw', 'Action, Test, Wizard'),
            ('taw', 'Test, Action, Wizard'),
            ('w', 'Wizard only')
        ]
    )

    keep_existing = fields.Boolean(
        string='Keep existing',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help=('Check it to keep previously existing test assignments; '
              'otherwise they will be deleted and created again')
    )

    show_created_records = fields.Boolean(
        string='Show records ',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help=('Check it to display the test assignments created for training '
              'actions upon completion')
    )

    time_by = fields.Selection(
        string='Time by',
        required=True,
        readonly=False,
        index=False,
        default='test',
        help=False,
        selection=[('test', 'Test'), ('question', 'Question')]
    )

    available_time = fields.Float(
        string='Time',
        required=True,
        readonly=False,
        index=False,
        default=0.5,
        digits=(16, 2),
        help='Available time to complete the exercise'
    )

    lock_time = fields.Boolean(
        string='Lock time',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help=('Check to not allow the user to continue with ',
              'the test once the time has passed')
    )

    correction_scale_id = fields.Many2one(
        string='Correction scale',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_correction_scale_id(),
        help='Choose the scale of correction',
        comodel_name='academy.tests.correction.scale',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    def default_correction_scale_id(self):
        xid = 'academy_tests.academy_tests_correction_scale_default'
        return self.env.ref(xid)

    # -------------------------------------------------------------------------
    # Constrains: SQL and Python constraints.
    # -------------------------------------------------------------------------

    _sql_constraints = [
        (
            'POSITIVE_INTERVAL',
            'CHECK(expiration > release)',
            _(u'The expiration date must be greater than the publication date')
        )
    ]

    @api.constrains('test_ids')
    def _check_test_ids(self):
        msg = _('No tests have been selected to assign in the wizard (#{})')

        for record in self:
            if not record.test_ids:
                raise ValidationError(msg.format(record.id))

    @api.constrains('training_action_ids')
    def _check_training_action_ids(self):
        msg = _('No training actions have been selected to assign tests in '
                'the wizard (#{})')

        for record in self:
            if not record.training_action_ids:
                raise ValidationError(msg.format(record.id))

    # -------------------------------------------------------------------------
    # Methods: _log_assignment_already_exists and _log_assignment_was_created
    #
    # These are used to log certain events.
    # -------------------------------------------------------------------------

    @staticmethod
    def _log_assignment_already_exists(test, training_action, keep):
        pattern = ('Already exist an assignment for test #{} and '
                   'training action #{}. {}.')
        action = _('Skipping') if keep else _('Removing')
        message = pattern.format(test.id, training_action.id, action)
        _logger.warning(message)

    @staticmethod
    def _log_assignment_was_created(test, training_action):
        message = ('New assignment for test #{} and training action #{} has '
                   'been created.')
        _logger.debug(message.format(test.id, training_action.id))

    # -------------------------------------------------------------------------
    # Methods: _search_for_existing_assignments and _tackle_existing_assignment
    #
    # These are used to deal with existing assignments.
    # -------------------------------------------------------------------------

    @api.model
    def _search_for_existing_assignments(self, training_action, test):
        """Searches for existing assignments that match a given training action
        and test.

        Args:
            training_action (Record): The training action record to search
                                      assignments for.
            test (Record): The test record to search assignments for.

        Returns:
            RecordSet: A set of assignments that match the given test and
                       training action.
        """
        assignment_domain = [
            '&',
            ('test_id', '=', test.id),
            ('training_action_id', '=', training_action.id)
        ]
        assignment_obj = self.env['academy.tests.test.training.assignment']
        assignment_set = assignment_obj.search(assignment_domain)

        return assignment_set

    @api.model
    def _tackle_existing_assignment(self, training_action, test):
        """Handles existing assignments based on the wizard's 'keep_existing'
        setting.

        If an existing assignment is found and 'keep_existing' is False, it
        will be deleted. Otherwise, it will be retained.

        Args:
            training_action (Record): The training action associated with the
                                      assignment.
            test (Record): The test associated with the assignment.

        Returns:
            bool: True if the assignment should be tackled (created or
                  updated), False if it should be left as is.
        """
        tackle = True

        existing_set = self._search_for_existing_assignments(
            training_action, test)

        if existing_set:
            self._log_assignment_already_exists(
                test, training_action, self.keep_existing)

            if not self.keep_existing:
                existing_set.unlink()
            else:
                tackle = False

        return tackle

    # -------------------------------------------------------------------------
    # Methods: _update_training_action, _update_test, _update_time,
    #          _update_scale and _update_name
    #
    # These are used to update the dictionary of values required to create each
    # one of the new assignments.
    # -------------------------------------------------------------------------

    @staticmethod
    def _update_training_action(values, training_action):
        training_ref = f'academy.training.action,{training_action.id}'
        values['training_ref'] = training_ref

    @staticmethod
    def _update_test(values, test):
        values['test_id'] = test.id

    def _update_time(self, values, test, action):
        """Updates the 'values' dictionary with time-related settings based on
        the wizard's configuration.

        Args:
            values (dict): The dictionary of values to be updated.
            test (Record): The test record used for time settings.
            action (Record): The training action record used for time settings.

        Raises:
            ValueError: If an unexpected value is encountered in the
                        'use_options' attribute.
        """

        self.ensure_one()

        w_time = self.available_time
        w_time_by = self.time_by
        w_lock_time = self.lock_time

        a_isset = action and action.available_time
        a_time = action.available_time if a_isset else w_time
        a_time_by = 'test' if a_isset else w_time_by
        a_lock_time = True if a_isset else w_lock_time

        t_isset = test and test.available_time
        t_time = test.available_time if t_isset else w_time
        t_time_by = test.time_by if t_isset else w_time_by
        t_lock_time = test.lock_time if t_isset else w_lock_time

        if self.use_options == 'aw':
            values['available_time'] = a_time
            values['time_by'] = a_time_by
            values['lock_time'] = a_lock_time
        elif self.use_options == 'tw':
            values['available_time'] = t_time
            values['time_by'] = t_time_by
            values['lock_time'] = t_lock_time
        elif self.use_options == 'atw':
            values['available_time'] = a_time if a_isset else t_time
            values['time_by'] = a_time_by if a_isset else t_time_by
            values['lock_time'] = a_lock_time if a_isset else t_lock_time
        elif self.use_options == 'taw':
            values['available_time'] = t_time if t_isset else a_time
            values['time_by'] = t_time_by if t_isset else a_time_by
            values['lock_time'] = t_lock_time if t_isset else a_lock_time
        elif self.use_options == 'w':
            values['available_time'] = w_time
            values['time_by'] = w_time_by
            values['lock_time'] = w_lock_time
        else:
            message = _('Unexpected value «{}» for attribute «Use options»')
            raise ValueError(message.format(self.user_options))

    def _update_scale(self, values, test, action):
        """Updates the 'values' dictionary with the correction scale ID based
        on the wizard's configuration.

        Args:
            values (dict): The dictionary of values to be updated.
            test (Record): The test record used for scale settings.
            action (Record): The training action record used for scale
                             settings.

        Raises:
            ValueError: If an unexpected value is encountered in the
                        'use_options' attribute.
        """
        self.ensure_one()

        w_scale = self.correction_scale_id.id

        a_isset = action and action.correction_scale_id
        a_scale = action.correction_scale_id.id if a_isset else w_scale

        t_isset = test and test.correction_scale_id
        t_scale = test.correction_scale_id.id if t_isset else w_scale

        if self.use_options == 'aw':
            values['correction_scale_id'] = a_scale
        elif self.use_options == 'tw':
            values['correction_scale_id'] = t_scale
        elif self.use_options == 'atw':
            values['correction_scale_id'] = a_scale if a_isset else t_scale
        elif self.use_options == 'taw':
            values['correction_scale_id'] = t_scale if a_isset else a_scale
        elif self.use_options == 'w':
            values['correction_scale_id'] = w_scale
        else:
            message = _('Unexpected value «{}» for attribute «Use options»')
            raise ValueError(message.format(self.user_options))

    def _update_name(self, values, test):
        """Updates the 'values' dictionary with a generated name for the
        assignment.

        Args:
            values (dict): The dictionary of values to be updated.
            test (Record): The test record used to generate the assignment
                           name.

        The method constructs a name from the test's name, the manager's name
        (if available), and the current date.
        """
        self.ensure_one()

        if self.manager_id and self.manager_id.name:
            manager = self.manager_id.name.split(' ')[0]
        else:
            manager = _('Unknown')

        dt = self.release or fields.Datetime.now()
        tz = get_tz(self.env)
        date_str = localized_dt(dt, tz, remove_tz=False).strftime('%x')

        values['name'] = f'{test.name} ({manager}, {date_str})'

    # -------------------------------------------------------------------------
    # Method: _show_created_assignments and perform_action
    # -------------------------------------------------------------------------

    @api.model
    def _show_created_assignments(self, assignment_set):
        """Summary

        Args:
            assignment_set (TYPE): Description

        Returns:
            TYPE: Description
        """
        action_xid = 'academy_tests.action_test_assignment_act_window'
        act_wnd = self.env.ref(action_xid)

        name = _('Created assignments')

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))
        context.update(search_default_my_assignments=0)

        domain = [('id', 'in', assignment_set.ids)]

        serialized = {
            'type': 'ir.actions.act_window',
            'res_model': act_wnd.res_model,
            'target': 'current',
            'name': name,
            'view_mode': act_wnd.view_mode,
            'domain': domain,
            'context': context,
            'search_view_id': act_wnd.search_view_id.id,
            'help': act_wnd.help
        }

        return serialized

    # -------------------------------------------------------------------------
    # Methods: _perform_action and perform_action
    # -------------------------------------------------------------------------

    def _perform_action(self):
        """Performs the main action of the wizard, creating test assignments
        to training actions.

        Creates and configures new assignments based on the selected tests and
        training actions, respecting the settings specified in the wizard.

        Returns:
            RecordSet: Set of records of the newly created assignments.
        """

        self.ensure_one()

        values = {
            'release': fields.Datetime.to_string(self.release),
            'expiration': fields.Datetime.to_string(self.expiration),
            'active': True,
            'validate_test': True
        }

        assignment_obj = self.env['academy.tests.test.training.assignment']
        assignment_set = self.env['academy.tests.test.training.assignment']

        for training_action in self.training_action_ids:
            self._update_training_action(values, training_action)

            for test in self.test_ids:
                if not self._tackle_existing_assignment(training_action, test):
                    continue

                self._update_test(values, test)
                self._update_name(values, test)

                activity = training_action.training_activity_id
                self._update_time(values, test, activity)
                self._update_scale(values, test, activity)

                assignment = assignment_obj.create(values)
                self._log_assignment_was_created(test, training_action)

                assignment_set += assignment

        return assignment_set

    def perform_action(self):
        """Public wrapper to perform the main action of the wizard.

        This method manages the context to disable tracking during the
        operation and aggregates the new assignments created by each record of
        the wizard.

        Returns:
            dict or None: If 'show_created_records' is enabled, returns a
                          dictionary for the window action.
        """
        tracking_disable_ctx = self.env.context.copy()
        tracking_disable_ctx.update({'tracking_disable': True})
        self = self.with_context(tracking_disable_ctx)

        assignment_set = self.env['academy.tests.test.training.assignment']

        for record in self:
            assignment_set += record._perform_action()

        if all(record.show_created_records for record in self):
            return self._show_created_assignments(assignment_set)
