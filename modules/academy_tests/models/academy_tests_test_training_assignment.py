# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.addons.academy_base.utils.record_utils import get_training_activity
from odoo.addons.academy_base.utils.record_utils import has_changed
from odoo.tools import safe_eval
from odoo.exceptions import AccessError, ValidationError, UserError
from odoo.osv.expression import TRUE_DOMAIN

from logging import getLogger

from datetime import time, datetime
from psycopg2.errors import SerializationFailure
from dateutil.relativedelta import relativedelta
from psycopg2 import Error as Psycopg2Error
from time import sleep

_logger = getLogger(__name__)


MODEL_ALLOW_SECONDARY = {
    'academy.training.action.enrolment': True,
    'academy.training.action': True,
    'academy.training.activity': True,
    'academy.competency.unit': False,
    'academy.training.module': False
}

MAX_RETRIES = 5


class AcademyTestsTestTrainingAssignment(models.Model):
    """ Allow users to assign test to training actions, training activities,
    competency units, training modules or training units
    """

    _name = 'academy.tests.test.training.assignment'
    _description = u'Academy tests test training assignment'

    _rec_name = 'name'
    _order = 'release DESC'

    _inherit = [
        'academy.abstract.training.reference',
        'ownership.mixin',
        'mail.thread'
    ]

    _check_company_auto = True

    company_id = fields.Many2one(
        string='Company',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Available for company',
        comodel_name='res.company',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        compute='_compute_company_id',
        store=True
    )

    @api.depends('enrolment_id', 'enrolment_id.training_action_id')
    def _compute_company_id(self):
        for record in self:
            if record.enrolment_id:
                record.company_id = record.enrolment_id.company_id
            elif record.training_action_id:
                record.company_id = record.training_action_id.company_id
            else:
                record.company_id = None

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self.default_name(),
        help='Enter new name',
        size=255,
        translate=True
    )

    def default_name(self):
        uid = self.env.context.get('uid', 1)
        user = self.env['res.users'].browse(uid)
        now = fields.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return 'Test from {} - {}'.format(user.name, now)

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=True,
        default=True,
        help=('If the active field is set to false, it will allow you to '
              'hide record without removing it'),
        track_visibility='onchange'
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Enter new description',
        translate=True
    )

    test_id = fields.Many2one(
        string='Test',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Test will be assigned to the chosen training item',
        comodel_name='academy.tests.test',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    random_template_id = fields.Many2one(
        string='Template ',
        readonly=True,
        related="test_id.random_template_id"
    )

    secondary_id = fields.Many2one(
        string='Sub-assignment',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.competency.unit',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    release = fields.Datetime(
        string='Release',
        required=True,
        readonly=False,
        index=True,
        default=fields.datetime.now(),
        help='Date and time from which the test will be available'
    )

    expiration = fields.Datetime(
        string='Expiration',
        required=True,
        readonly=False,
        index=True,
        default=datetime.now() + relativedelta(years=100),
        help='Date and time from which the test will be available'
    )

    time_by = fields.Selection(
        string='Time by',
        required=True,
        readonly=False,
        index=False,
        default='test',
        help='Specify if the available time is per test or per question',
        selection=[('test', 'Test'), ('question', 'Question')]
    )

    available_time = fields.Float(
        string='Time',
        required=True,
        readonly=False,
        index=False,
        default=0.5,
        digits=(8, 6),
        help='Available time per test or question to complete the exercise'
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

    enrolment_id = fields.Many2one(
        string='Enrolment',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='The enrolment to which the test will be assigned',
        comodel_name='academy.training.action.enrolment',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    training_action_id = fields.Many2one(
        string='Training action',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='The training action to which the test will be assigned',
        comodel_name='academy.training.action',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    training_activity_id = fields.Many2one(
        string='Training activity',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='The training activity to which the test will be assigned',
        comodel_name='academy.training.activity',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    competency_unit_id = fields.Many2one(
        string='Competency unit',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='The competency unit to which the test will be assigned',
        comodel_name='academy.competency.unit',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    training_module_id = fields.Many2one(
        string='Training module',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='The training module to which the test will be assigned',
        comodel_name='academy.training.module',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    attempt_ids = fields.One2many(
        string='Attempts',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Test attempts by students',
        comodel_name='academy.tests.attempt',
        inverse_name='assignment_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    # Will be filled by fast_update_attempt_data method
    attempt_count = fields.Integer(
        string='Attempt count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help=('Total number of attempts related to the current individual'
              'assignment.'),
        store=True
    )

    enrolment_ids = fields.Many2manyView(
        string='Enrolments',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='List with all the enrolments who can take the test',
        comodel_name='academy.training.action.enrolment',
        relation='academy_tests_test_training_assignment_enrolment_rel',
        column1='assignment_id',
        column2='enrolment_id',
        domain=[],
        context={},
        limit=None,
        copy=False
    )

    enrolment_count = fields.Integer(
        string='Nº enrolments',
        required=False,
        readonly=True,
        index=False,
        default=0,
        store=False,
        help='Show number of enrolments who can take the test',
        compute='_compute_enrolment_count'
    )

    @api.depends('enrolment_ids')
    def _compute_enrolment_count(self):
        for record in self:
            record.enrolment_count = len(record.enrolment_ids)

    student_ids = fields.Many2manyView(
        string='Students',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='List with all the students who can take the test',
        comodel_name='academy.student',
        relation='academy_tests_test_training_assignment_student_rel',
        column1='assignment_id',
        column2='student_id',
        domain=[],
        context={},
        limit=None,
        copy=False
    )

    student_count = fields.Integer(
        string='Nº students',
        required=False,
        readonly=True,
        index=False,
        default=0,
        store=False,
        help='Show number of students who can take the test',
        compute='_compute_student_count'
    )

    @api.depends('student_ids')
    def _compute_student_count(self):
        for record in self:
            record.student_count = len(record.student_ids)

    secondary_activity_id = fields.Many2one(
        string='Secondary activity',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Value will be used to compute secodary_id field domain',
        comodel_name='academy.training.activity',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        store=False,
        compute='_compute_secondary_activity_id'
    )

    @api.depends('training_ref')
    def _compute_secondary_activity_id(self):
        for record in self:
            record.secondary_activity_id = record._get_activity()

    validate_test = fields.Boolean(
        string='Check test',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to validate test before save'
    )

    def _check_topics_and_categories(self):
        result = False

        for record in self:
            test_topic_ids, test_category_ids = \
                record._get_test_categorization()
            training_topic_ids, training_category_ids = \
                record._get_training_categorization()

            extra_topic_ids = [topic_id for topic_id in test_topic_ids
                               if topic_id not in training_topic_ids]

            extra_cat_ids = [category_id for category_id in test_category_ids
                             if category_id not in training_category_ids]

            result = not extra_topic_ids and not extra_cat_ids

            if not result:
                break

        return result

    def _get_test_categorization(self):
        question_set = self.mapped('test_id.question_id.question_id')

        topic_ids = question_set.mapped('topic_id.id')
        category_ids = question_set.mapped('category_ids.id')

        return topic_ids, category_ids

    def _get_training_categorization(self):
        record_set = self.mapped('training_ref')

        if self.training_ref._name == 'academy.training.action.enrolment':
            record_set = record_set.mapped('training_action_id')

        if self.training_ref._name == 'academy.training.action':
            record_set = record_set.mapped('training_activity_id')

        if self.training_ref._name == 'academy.training.activity':
            record_set = record_set.mapped('secondary_ids')

        if self.training_ref._name == 'academy.competency.unit':
            record_set = record_set.mapped('training_module_ids')

        topic_ids = record_set.mapped('available_topic_ids.id')
        category_ids = record_set.mapped('available_categories_ids.id')

        return topic_ids, category_ids

    first_attempt_id = fields.Many2one(
        string='First attempt',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help=('Reference to the first attempt at the assigned test for this '
              'assignment.'),
        comodel_name='academy.tests.attempt',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    last_attempt_id = fields.Many2one(
        string='Last attempt',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help=('Reference to the most recent attempt at the assigned test for '
              'this assignment.'),
        comodel_name='academy.tests.attempt',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    best_attempt_id = fields.Many2one(
        string='Best attempt',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help=('Reference to the highest scoring attempt at the assigned test '
              'for this assignment.'),
        comodel_name='academy.tests.attempt',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    first_attempt = fields.Datetime(
        string='First attempt datetime',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Date and time when the first attempt was completed'
    )

    last_attempt = fields.Datetime(
        string='Last attempt datetime',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Date and time when the last attempt was completed'
    )

    best_attempt = fields.Datetime(
        string='Best attempt datetime',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Date and time when the best attempt was completed'
    )

    first_points = fields.Float(
        string='First points',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Points earned on the first attempt'
    )

    last_points = fields.Float(
        string='Last points',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Points earned on the last attempt'
    )

    best_points = fields.Float(
        string='Best points',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='Points earned on the best attempt'
    )

    first_student_id = fields.Many2one(
        string='First student',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Student who has obtained the highest score in the assigned test',
        comodel_name='academy.student',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    last_student_id = fields.Many2one(
        string='Last student',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Student who has taken the test for the first time',
        comodel_name='academy.student',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    best_student_id = fields.Many2one(
        string='Best student',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Student who has taken the test for the last time',
        comodel_name='academy.student',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    question_count = fields.Integer(
        string='Number of questions',
        required=False,
        readonly=False,
        index=False,
        default=0,
        help='Show the number of questions in test'
    )

    max_points = fields.Float(
        string='Max points',
        required=True,
        readonly=True,
        index=False,
        default=0.0,
        digits=(16, 2),
        help='The maximum points achievable in an attempt'
    )

    @api.depends('question_count', 'correction_scale_id')
    def _compute_max_points(self):
        for record in self:
            record.max_points = \
                record.question_count * record.correction_scale_id.right

    max_final_points = fields.Float(
        string='MAX final points',
        required=True,
        readonly=True,
        index=True,
        default=0.0,
        digits=(16, 2),
        help=('Maximum of points from final answers in the attempts of this '
              'assignment')
    )

    min_final_points = fields.Float(
        string='MIN final points',
        required=True,
        readonly=True,
        index=True,
        default=0.0,
        digits=(16, 2),
        help=('Minimum of points from final answers in the attempts of this '
              'assignment')
    )

    avg_final_points = fields.Float(
        string='AVG final points',
        required=True,
        readonly=True,
        index=True,
        default=0.0,
        digits=(16, 2),
        help=('Average of points from final answers in the attempts of this '
              'assignment')
    )

    avg_right_points = fields.Float(
        string='AVG right points',
        required=True,
        readonly=True,
        index=True,
        default=0.0,
        digits=(16, 2),
        help=('Average of points from right answers in the attempts of this '
              'assignment')
    )

    avg_wrong_points = fields.Float(
        string='AVG wrong points',
        required=True,
        readonly=True,
        index=True,
        default=0.0,
        digits=(16, 2),
        help=('Average of points from wrong answers in the attempts of this '
              'assignment')
    )

    avg_blank_points = fields.Float(
        string='AVG blank points',
        required=True,
        readonly=True,
        index=True,
        default=0.0,
        digits=(16, 2),
        help=('Average of points from blank answers in the attempts of this '
              'assignment')
    )

    avg_answered_count = fields.Integer(
        string='AVG answered count',
        required=True,
        readonly=True,
        index=True,
        default=0,
        help=('Average number of answered questions in the attempts of this '
              'assignment')
    )

    avg_right_count = fields.Integer(
        string='AVG right count',
        required=True,
        readonly=True,
        index=True,
        default=0,
        help=('Average number of right answers in the attempts of this '
              'assignment')
    )

    avg_wrong_count = fields.Integer(
        string='AVG wrong count',
        required=True,
        readonly=True,
        index=True,
        default=0,
        help=('Average number of wrong answers in the attempts of this '
              'assignment')
    )

    avg_blank_count = fields.Integer(
        string='AVG blank count',
        required=True,
        readonly=True,
        index=True,
        default=0,
        help=('Average number of blank questions in the attempts of this '
              'assignment')
    )

    passed_count = fields.Integer(
        string='Passed count',
        required=True,
        readonly=True,
        index=True,
        default=0,
        help=('Number of passed attempts')
    )

    failed_count = fields.Integer(
        string='Failed count',
        required=True,
        readonly=True,
        index=True,
        default=0,
        help=('Number of failed attempts')
    )

    # -------------------------------------------------------------------------
    # CONSTRAINTS
    # -------------------------------------------------------------------------

    _sql_constraints = [
        (
            'mandaroty_training_ref',
            'CHECK(training_type IS NOT NULL AND training_ref IS NOT NULL)',
            _(u'You must set a training item')
        ),
        (
            'positive_available_interval',
            'CHECK(expiration > release)',
            _(u'Expiration date must be later than release date')
        ),
        (
            'single_assignment',
            'UNIQUE(test_id, training_ref)',
            _(u'Assignment of test to training is duplicated')
        ),
        (
            'positive_available_time',
            'CHECK(available_time > 0)',  # It can be zero if not set
            _(u'Available time attribute must have a positive value')
        )
    ]

    # -------------------------------------------------------------------------
    # Extend parent abstract model
    # -------------------------------------------------------------------------

    @api.onchange('training_ref')
    def _onchange_training_ref(self):

        _super = super(AcademyTestsTestTrainingAssignment, self)
        _super._onchange_training_ref()

        if self.training_ref and has_changed(self, 'training_ref'):
            self.update_realization_attributes()

    @api.onchange('test_id')
    def _onchange_test_id(self):

        if self.test_id:
            if has_changed(self, 'test_id'):
                if self.test_id.name:
                    self.name = self.test_id.name

                self.update_realization_attributes()
        else:
            self.default_name()

    def update_realization_attributes(self):
        for record in self:
            activity = get_training_activity(record.env, record.training_ref)
            test = record.test_id

            if test and test.correction_scale_id:
                record.correction_scale_id = test.correction_scale_id
            elif activity and activity.correction_scale_id:
                record.correction_scale_id = activity.correction_scale_id
            else:
                record.correction_scale_id = self.default_correction_scale_id()

            if test and test.available_time:
                record.available_time = test.available_time or 0.5
                record.time_by = test.time_by
                record.lock_time = test.lock_time
            elif activity and activity.available_time:
                record.available_time = test.available_time or 0.5
                record.time_by = 'test'
                record.lock_time = True
            else:
                field_names = ['available_time', 'time_by', 'lock_time']
                defaults = record.default_get(field_names)
                record.available_time = defaults.get('available_time', 0.5)
                record.time_by = defaults.get('time_by', 'test')
                record.lock_time = defaults.get('lock_time', False)

    @api.model
    def _ensure_consistency_in_training(self, values, create=False):
        """Extends parent abstract model method removing secondary_id value
        if it is not allowed. To get more information see the parent method
        description.
        """

        _super = super(AcademyTestsTestTrainingAssignment, self)
        model, id_str = _super._ensure_consistency_in_training(values, create)

        if model and MODEL_ALLOW_SECONDARY[model] is False:
            values['secondary_id'] = None

        return model, id_str

    # -------------------------------------------------------------------------
    # Overridden Non-CRUD Methods
    # -------------------------------------------------------------------------

    @api.depends('training_ref', 'test_id')
    def name_get(self):
        result = []

        display = self.env.context.get('name_get', None)
        pattern = _('Assigning test #{} to {} #{}')

        for record in self:
            if isinstance(record.id, models.NewId):
                name = _('New assignment')
            elif display == 'test':
                name = record.test_id.display_name
            elif display == 'training':
                name = record.training_ref.display_name
            else:
                training_type = record.get_training_type_name().lower()
                training_ref = record.training_ref.id
                test_id = record.test_id.id
                name = pattern.format(test_id, training_type, training_ref)

            result.append((record.id, name))

        return result

    # -------------------------------------------------------------------------
    # Auxilary methods
    # -------------------------------------------------------------------------

    def _get_activity(self):
        self.ensure_one()

        if not self.training_ref:
            activity_id = False
        elif self.training_ref._name == 'academy.training.action.enrolment':
            action_item = self.training_ref.training_action_id
            activity_id = action_item.training_activity_id
        elif self.training_ref._name == 'academy.training.action':
            activity_id = self.training_ref.training_activity_id
        elif self.training_ref._name == 'academy.training.activity':
            activity_id = self.training_ref
        else:
            activity_id = False

        return activity_id

    # -------------------------------------------------------------------------
    # Actions and Events
    # -------------------------------------------------------------------------

    def view_test_attempts(self):
        self.ensure_one()

        action_xid = 'academy_tests.action_test_attempts_act_window'
        act_wnd = self.env.ref(action_xid)

        name = _('Attempts')

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))
        context.update({'default_assignment_id': self.id})

        domain = [('assignment_id', '=', self.id)]

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

    def view_students(self):
        self.ensure_one()

        return {
            'model': 'ir.actions.act_window',
            'type': 'ir.actions.act_window',
            'name': _('Students'),
            'res_model': 'academy.student',
            'target': 'current',
            'view_mode': 'kanban,tree,form',
            'domain': [('id', 'in', self.mapped('student_ids.id'))],
            'context': {}
        }

    def view_individual_assignments(self):
        self.ensure_one()

        action_xid = 'academy_tests.action_single_assignments_act_window'
        act_wnd = self.env.ref(action_xid)

        name = _('Individual assignments')

        rel_mod = 'academy.tests.test.training.assignment.enrolment.rel'
        rel_obj = self.env[rel_mod]
        uperm = rel_obj.check_access_rights('write', raise_exception=False)
        dperm = rel_obj.check_access_rights('unlink', raise_exception=False)
        if uperm and dperm:
            rel_obj.purge_obsolete_records(assignments=self)
            rel_obj.generate_missing_records(assignments=self)

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))
        context.update({'default_assignment_id': self.id})

        domain = [('assignment_id', '=', self.id)]

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
    # Update academy.tests.test to be used from test assignment
    # -------------------------------------------------------------------------

    def save_as_docx(self):
        self.ensure_one()

        return self.test_id.save_as_docx()

    def download_as_moodle_xml(self):
        self.ensure_one()

        return self.test_id.download_as_moodle_xml()

    def new_from_template(self, gui=True):
        self.ensure_one()

        now = fields.datetime.now()
        available = self.expiration - self.release

        release = max(self.release, now)
        expiration = release + available

        context = self.env.context
        training_ref = self.training_ref
        training_ref = context.get('default_training_ref', training_ref)

        test_id = self.test_id.new_from_template(gui=False)
        assignment = self.copy({
            'test_id': test_id.id,
            'release': release,
            'expiration': expiration,
            'owner_id': self.env.context.get('uid', self.owner_id.id),
            'training_ref': training_ref
        })

        if gui:
            return {
                'model': 'ir.actions.act_window',
                'type': 'ir.actions.act_window',
                'name': assignment.name,
                'res_model': self._name,
                'target': 'current',
                'view_mode': 'form',
                'res_id': assignment.id,
                'context': {}
            }

    def download_as_pdf(self):
        self.ensure_one()

        return self.test_id.download_as_pdf()

    # -------------------------------------------------------------------------
    # RECONCILE RECORDS
    # -------------------------------------------------------------------------

    def _old_fast_update_attempt_data(self):
        """
        Updates attempt-related data for each individual assignment by
        executing an SQL query that computes first, last, and best attempts,
        among other data. This query handles missing information by filling in
        default values.

        If self contains records, the update is restricted to those records;
        otherwise, the update is applied to all records in the database.

        This method does not use ORM; instead, it performs updates using a
        complex SQL query.
        """

        sql_pattern = '''
        WITH targets AS (

            -- This CTE is used only to limit the records to be considered
            SELECT
                "id" AS assignment_id,
                test_id,
                correction_scale_id
            FROM
                academy_tests_test_training_assignment AS ass
            WHERE
                TRUE {restriction}

        ), test_question_count AS (

            SELECT
                link.test_id,
                COUNT ( atq."id" )::INTEGER AS question_count
            FROM
                academy_tests_test_question_rel AS link
            INNER JOIN academy_tests_question AS atq
                ON atq."id" = link.question_id
                AND atq.active
            INNER JOIN targets AS tgs
                ON tgs.test_id = link.test_id
            GROUP BY
                link.test_id

        ), attempt_info AS (

            -- Obtains the first, last, and best attempt for each
            -- global assignment. It does not take into account those
            -- that are still open

            SELECT DISTINCT ON ( att.assignment_id )
                att.assignment_id,
                FIRST_VALUE ( "id" ) OVER first_wnd AS first_attempt_id,
                FIRST_VALUE ( "id" ) OVER last_wnd AS last_attempt_id,
                FIRST_VALUE ( "id" ) OVER best_wnd AS best_attempt_id
            FROM
                academy_tests_attempt AS att
            INNER JOIN targets AS tgs
                ON tgs.assignment_id = att.assignment_id
            WHERE
                active
                AND closed
            WINDOW
                first_wnd AS (
                    PARTITION BY att.assignment_id
                    ORDER BY "start" ASC, create_date ASC
                ),
                last_wnd AS (
                    PARTITION BY att.assignment_id
                    ORDER BY "start" DESC, create_date DESC
                ),
                best_wnd AS (
                    PARTITION BY att.assignment_id
                    ORDER BY final_points DESC, create_date ASC
                )
            ORDER BY
                att.assignment_id

        ) , attempt_count AS (

            -- Counts attempts for each global assignment. It takes
            -- into account those that are still open.

            SELECT
                att.assignment_id,

                COUNT ( "id" ) :: INTEGER AS attempt_count,
                MAX ( final_points ) :: FLOAT AS max_final_points,
                MIN ( final_points ) :: FLOAT AS min_final_points,

                AVG ( final_points ) :: FLOAT AS avg_final_points,
                AVG ( right_points ) :: FLOAT AS avg_right_points,
                AVG ( wrong_points ) :: FLOAT AS avg_wrong_points,
                AVG ( blank_points ) :: FLOAT AS avg_blank_points,

                AVG ( answered_count )::INT AS avg_answered_count,
                AVG ( right_count ) :: INT AS avg_right_count,
                AVG ( wrong_count ) :: INT AS avg_wrong_count,
                AVG ( blank_count ) :: INT AS avg_blank_count,

                SUM ( passed::INT ) :: INTEGER AS passed_count,
                SUM ( (NOT passed)::INT ) :: INTEGER AS failed_count
            FROM
                academy_tests_attempt AS att
            INNER JOIN targets AS tgs
                ON tgs.assignment_id = att.assignment_id
            WHERE
                active
            GROUP BY
                att.assignment_id

        ), computed_data AS (
            -- Completes missing information, such as dates or scores, and
            -- fills records with no information with default values.

            SELECT
                tgs.assignment_id,

                tqc.question_count,
                (
                    tqc.question_count::FLOAT * "scale"."right"
                )::FLOAT AS max_points,

                info.first_attempt_id,
                info.last_attempt_id,
                info.best_attempt_id,

                fa."end" AS first_attempt,
                la."end" AS last_attempt,
                ba."end" AS best_attempt,

                fa.student_id AS first_student_id,
                la.student_id AS last_student_id,
                ba.student_id AS best_student_id,

                COALESCE( fa."final_points", 0.0 )::FLOAT AS first_points,
                COALESCE( la."final_points", 0.0 )::FLOAT AS last_points,
                COALESCE( ba."final_points", 0.0 )::FLOAT AS best_points,

                COALESCE( ac.attempt_count, 0 )::INTEGER AS attempt_count,

                -- Same as la.final_points
                COALESCE( ac.max_final_points, 0.0)::FLOAT AS max_final_points,
                COALESCE( ac.min_final_points, 0.0)::FLOAT AS min_final_points,

                COALESCE( avg_final_points, 0.0 )::FLOAT AS avg_final_points,
                COALESCE( avg_right_points, 0.0 )::FLOAT AS avg_right_points,
                COALESCE( avg_wrong_points, 0.0 )::FLOAT AS avg_wrong_points,
                COALESCE( avg_blank_points, 0.0 )::FLOAT AS avg_blank_points,

                COALESCE( avg_answered_count,0.0)::INT AS avg_answered_count,
                COALESCE( avg_right_count, 0.0 )::INT AS avg_right_count,
                COALESCE( avg_wrong_count, 0.0 )::INT AS avg_wrong_count,
                COALESCE( avg_blank_count, 0.0 )::INT AS avg_blank_count,

                COALESCE( passed_count, 0 )::INTEGER AS passed_count,
                COALESCE( failed_count, 0 )::INTEGER AS failed_count
            FROM
                targets AS tgs
            INNER JOIN test_question_count AS tqc
                ON tqc."test_id" = tgs.test_id
            INNER JOIN academy_tests_correction_scale AS "scale"
                ON "scale"."id" = tgs.correction_scale_id
            LEFT JOIN attempt_info AS info
                ON tgs.assignment_id = info.assignment_id
            LEFT JOIN academy_tests_attempt AS fa
                ON fa."id" = info.first_attempt_id
            LEFT JOIN academy_tests_attempt AS la
                ON la."id" = info.last_attempt_id
            LEFT JOIN academy_tests_attempt AS ba
                ON ba."id" = info.best_attempt_id
            LEFT JOIN attempt_count AS ac
                ON ac.assignment_id = info.assignment_id
        )
        UPDATE academy_tests_test_training_assignment AS ass
        SET
            question_count = cd.question_count,
            max_points = cd.max_points,
            first_attempt_id = cd.first_attempt_id,
            last_attempt_id = cd.last_attempt_id,
            best_attempt_id = cd.best_attempt_id,
            first_attempt = cd.first_attempt,
            last_attempt = cd.last_attempt,
            best_attempt = cd.best_attempt,
            first_student_id = cd.first_student_id,
            last_student_id = cd.last_student_id,
            best_student_id = cd.best_student_id,
            first_points = cd.first_points,
            last_points = cd.last_points,
            best_points = cd.best_points,
            attempt_count = cd.attempt_count,
            max_final_points = cd.max_final_points,
            min_final_points = cd.min_final_points,
            avg_final_points = cd.avg_final_points,
            avg_right_points = cd.avg_right_points,
            avg_wrong_points = cd.avg_wrong_points,
            avg_blank_points = cd.avg_blank_points,
            avg_answered_count = cd.avg_answered_count,
            avg_right_count = cd.avg_right_count,
            avg_wrong_count = cd.avg_wrong_count,
            avg_blank_count = cd.avg_blank_count,
            passed_count = cd.passed_count,
            failed_count = cd.failed_count
        FROM
            computed_data AS cd
        WHERE
            cd.assignment_id = ass."id"
        '''

        try:
            self.check_access_rights('write')
        except AccessError:
            message = _('You do not have the necessary permissions to update '
                        'this data.')
            raise UserError(message)

        if self:
            ids_str = ', '.join([str(record.id) for record in self])
            restriction = f' AND ass."id" IN ({ids_str}) '
        else:
            restriction = ''

        sql = sql_pattern.format(restriction=restriction)
        self._execute_query(sql, notify=True, action='update_attempt_data')

    @api.model
    def _execute_query(self, sql, selection=False, notify=False, action=None):
        results = []
        action = action or 'SQL'

        for attempt in range(MAX_RETRIES):
            try:
                cursor = self.env.cr
                cursor.execute(sql)

                if selection:
                    results = cursor.dictfetchall()

                break

            except SerializationFailure:
                if attempt < MAX_RETRIES - 1:
                    message = 'Failed to execute SQL {} / {} tries'
                    _logger.warning(message.format(attempt, MAX_RETRIES))
                    sleep(1)  # Wait before retry
                else:
                    if notify:
                        message = _('Failed to execute {} after {} tries')
                        raise UserError(message.format(action, MAX_RETRIES))
                    else:
                        message = 'Failed to execute {} after {} tries'
                        _logger.error(message.format(action, MAX_RETRIES))

            except Exception as ex:
                if notify:
                    message = _('Failed to execute {}. System says: {}')
                    raise UserError(message.format(action, ex))
                else:
                    message = 'Failed to execute {}. System says: {}'
                    _logger.error(message.format(action, ex))

                break

        return results if selection else True

    def reconcile_records(self, full_db=False):
        record_set = self.search(TRUE_DOMAIN) if full_db else self

        ind_model = 'academy.tests.test.training.assignment.enrolment.rel'
        self.env[ind_model].reconcile_records(assignments=record_set)

        record_set.fast_update_attempt_data()

    @api.model
    def _get_default_attempt_data(self):
        return {
            'question_count': 0,
            'max_points': 0.0,
            'first_attempt_id': None,
            'last_attempt_id': None,
            'best_attempt_id': None,
            'first_attempt': None,
            'last_attempt': None,
            'best_attempt': None,
            'first_student_id': None,
            'last_student_id': None,
            'best_student_id': None,
            'first_points': 0.0,
            'last_points': 0.0,
            'best_points': 0.0,
            'attempt_count': 0,
            'max_final_points': 0.0,
            'min_final_points': 0.0,
            'avg_final_points': 0.0,
            'avg_right_points': 0.0,
            'avg_wrong_points': 0.0,
            'avg_blank_points': 0.0,
            'avg_answered_count': 0,
            'avg_right_count': 0,
            'avg_wrong_count': 0,
            'avg_blank_count': 0,
            'passed_count': 0,
            'failed_count': 0,
        }

    def _compute_attempt_data(self):
        values = self._get_default_attempt_data()

        scale = self.correction_scale_id
        values['question_count'] = len(self.test_id.question_ids)
        values['max_points'] = values['question_count'] * scale.right

        if self.attempt_ids:
            attempt_count = len(self.attempt_ids)
            values['attempt_count'] = attempt_count

            first_attempt = self.attempt_ids.sorted(
                key=lambda r: r.start, reverse=False)[0]
            values['first_attempt_id'] = first_attempt.id
            values['first_attempt'] = first_attempt.end
            values['first_points'] = first_attempt.final_points
            values['first_student_id'] = \
                first_attempt.enrolment_id.student_id.id

            last_attempt = self.attempt_ids.sorted(
                key=lambda r: r.start, reverse=True)[0]
            values['last_attempt_id'] = last_attempt.id
            values['last_attempt'] = last_attempt.end
            values['last_points'] = last_attempt.final_points
            values['last_student_id'] = \
                last_attempt.enrolment_id.student_id.id

            best_attempt = self.attempt_ids.sorted(
                key=lambda r: r.final_points, reverse=True)[0]
            values['best_attempt_id'] = best_attempt.id
            values['best_attempt'] = best_attempt.end
            values['best_points'] = best_attempt.final_points
            values['best_student_id'] = \
                best_attempt.enrolment_id.student_id.id

            final_points_list = self.mapped('attempt_ids.final_points')
            values['max_final_points'] = max(final_points_list)
            values['min_final_points'] = min(final_points_list)
            values['avg_final_points'] = \
                self._safe_division(sum(final_points_list), attempt_count, 0.0)

            right_points_list = self.mapped('attempt_ids.right_points')
            wrong_points_list = self.mapped('attempt_ids.wrong_points')
            blank_points_list = self.mapped('attempt_ids.blank_points')
            values['avg_right_points'] = \
                self._safe_division(sum(right_points_list), attempt_count, 0.0)
            values['avg_wrong_points'] = \
                self._safe_division(sum(wrong_points_list), attempt_count, 0.0)
            values['avg_blank_points'] = \
                self._safe_division(sum(blank_points_list), attempt_count, 0.0)

            right_count_list = self.mapped('attempt_ids.right_count')
            wrong_count_list = self.mapped('attempt_ids.wrong_count')
            blank_count_list = self.mapped('attempt_ids.blank_count')
            values['avg_right_count'] = \
                self._safe_division(sum(right_count_list), attempt_count, 0)
            values['avg_wrong_count'] = \
                self._safe_division(sum(wrong_count_list), attempt_count, 0)
            values['avg_blank_count'] = \
                self._safe_division(sum(blank_count_list), attempt_count, 0)

            answered_count_list = self.mapped('attempt_ids.answered_count')
            values['avg_answered_count'] = \
                self._safe_division(sum(answered_count_list), attempt_count, 0)

            passed_count = len(self.attempt_ids.filtered(lambda r: r.passed))
            values['passed_count'] = passed_count
            values['failed_count'] = attempt_count - passed_count

        return values

    def fast_update_attempt_data(self):
        for record in self:
            values = record._compute_attempt_data()
            record.write(values)

    @staticmethod
    def _safe_division(dividend, divisor, default=0.0):
        try:
            result = dividend / divisor
            result = type(default)(result)
        except ZeroDivisionError:
            message = (f'Warning: Division by zero. '
                       f'Returning {default} as the result.')
            _logger.warning(message)
            result = default
        except (ValueError, TypeError) as e:
            message = (f'Warning: Invalid input {e}. '
                       f'Returning {default} as the result.')
            _logger.warning(message)
            result = default

        return result

    # -------------------------------------------------------------------------
    # Public methods
    # -------------------------------------------------------------------------

    def get_available_time(self):
        """
        Compute the total available time for completing the exercise.

        This method calculates the available time based on the configured time
        per test or question. If the time is set by question, it multiplies the
        available time by the number of questions in the test. If there are no
        questions, it defaults to at least one.

        Returns:
            float: The computed total available time.
        """
        self.ensure_one()

        available_time = self.available_time

        if self.time_by == 'question' and self.test_id:
            question_count = len(self.test_id.question_ids) or 1
            available_time *= question_count

        return available_time
