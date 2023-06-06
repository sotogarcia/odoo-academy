# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger

from datetime import datetime
from dateutil.relativedelta import relativedelta

_logger = getLogger(__name__)


MODEL_ALLOW_SECONDARY = {
    'academy.training.action.enrolment': True,
    'academy.training.action': True,
    'academy.training.activity': True,
    'academy.competency.unit': False,
    'academy.training.module': False
}


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

    @api.depends('enrolment_id', 'training_action_id')
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
        index=False,
        default=True,
        help=('If the active field is set to false, it will allow you to '
              'hide record without removing it'),
        track_visibility='onchange'
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

    attempt_count = fields.Integer(
        string='Attempt count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of test attempts',
        store=False,
        compute='_compute_attempt_count'
    )

    @api.depends('attempt_ids')
    def _compute_attempt_count(self):
        for record in self:
            record.attempt_count = len(record.attempt_ids)

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

    @api.depends('student_ids')
    def _compute_student_count(self):
        for record in self:
            record.student_count = len(record.student_ids)

    @api.onchange('training_ref')
    def _onchange_training_ref(self):

        for record in self:
            _super = super(AcademyTestsTestTrainingAssignment, record)
            _super._onchange_training_ref()

            record._update_correction_scale_id()

            record.secondary_id = None

    @api.onchange('test_id')
    def _onchange_test_id(self):

        for record in self:
            if record.test_id:
                record.name = record.test_id.name
            else:
                record.name = record.default_name()

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
    ]

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

    def _update_correction_scale_id(self):
        self.ensure_one()

        if self.training_ref and \
           hasattr(self.training_ref, 'correction_scale_id') and \
           self.training_ref.correction_scale_id:
            scale_id = getattr(self.training_ref, 'correction_scale_id')

        else:
            scale_id = self.default_correction_scale_id()

        self.correction_scale_id = scale_id

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

    def view_test_attempts(self):
        self.ensure_one()

        irf = self.env.ref('academy_tests.ir_filter_assignment_attempts')

        return {
            'model': 'ir.actions.act_window',
            'type': 'ir.actions.act_window',
            'name': _('Test attempts'),
            'res_model': 'academy.tests.attempt.resume.helper',
            'target': 'current',
            'view_mode': 'pivot,tree,form,graph',
            'domain': [('assignment_id', '=', self.id)],
            'context': irf.context
        }

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
