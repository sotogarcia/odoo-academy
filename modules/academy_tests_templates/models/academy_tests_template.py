# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class AcademyTestsTemplate(models.Model):
    """ Template to create new tests
    """

    _name = 'academy.tests.template'
    _description = u'Template to create new tests'

    _inherit = [
        'ownership.mixin',
        'image.mixin',
        'mail.thread',
        'mail.activity.mixin',
        'academy.abstract.test'
    ]

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Enter new name',
        size=255,
        translate=True,
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

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Enables/disables the record'
    )

    line_ids = fields.One2many(
        string='Criteria',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.random.line',
        inverse_name='template_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None,
        copy=True
    )

    test_ids = fields.One2many(
        string='Used in',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.test',
        inverse_name='template_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None,
        copy=False
    )

    test_count = fields.Integer(
        string='Nº of tests',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show the number of test have been created using this template',
        compute='_compute_test_count'
    )

    quantity = fields.Integer(
        string='Quantity',
        required=True,
        readonly=False,
        index=False,
        default=0,
        help='Maximum number of questions can be appended',
        compute='_compute_quantity',
        wizard=True,
        store=False,
    )

    lines_count = fields.Integer(
        string='Nº lines',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of lines',
        store=False,
        compute='_compute_line_count'
    )

    # ------------------------ TEST INFORMATION ------------------------

    time_by = fields.Selection(
        string='Time by',
        required=False,
        readonly=False,
        index=False,
        default='test',
        help=False,
        selection=[('test', 'Test'), ('question', 'Question')],
        wizard=True
    )

    available_time = fields.Float(
        string='Time',
        required=False,
        readonly=False,
        index=False,
        default=0.5,
        digits=(16, 2),
        help='Available time to complete the exercise',
        wizard=True
    )

    lock_time = fields.Boolean(
        string='Lock time',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help=('Check to not allow the user to continue with the test once the '
              'time has passed'),
        wizard=True
    )

    correction_scale_id = fields.Many2one(
        string='Correction scale',
        required=False,
        readonly=False,
        index=False,
        default=lambda self: self.default_correction_scale_id(),
        help='Choose the scale of correction',
        comodel_name='academy.tests.correction.scale',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        wizard=True
    )

    test_kind_id = fields.Many2one(
        string='Kind of test',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_test_kind_id(),
        help='Choose the kind for this test',
        comodel_name='academy.tests.test.kind',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        wizard=True
    )

    test_description = fields.Text(
        string='Test description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about the test',
        translate=True,
        wizard=True
    )

    skip_faulty_lines = fields.Boolean(
        string='Skip faulty',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Check it to skip faulty lines',
        wizard=True
    )

    name_pattern = fields.Char(
        string='Name pattern',
        required=False,
        readonly=False,
        index=False,
        default='{template} %m/%d/%Y - {sequence}',
        help='Pattern will be used to create names to the new tests',
        size=1024,
        translate=True,
        wizard=True
    )

    parent_id = fields.Many2one(
        string='Parent',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose parent template',
        comodel_name='academy.tests.random.template',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    serial = fields.Integer(
        string='Serial',
        required=True,
        readonly=True,
        index=False,
        default=1,
        help='Number of test have been created using this template'
    )

    self_assignment = fields.Boolean(
        string='Self assignment',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Check it to self assign template to new created test',
    )

    # NEW: this field was added after migration
    training_ref = fields.Reference(
        string='Training',
        required=True,
        readonly=False,
        index=True,
        default=0,
        help='Training element: Enrolment, Action, Activity,...',
        selection=[
            ('academy.training.action.enrolment', 'Enrolment'),
            ('academy.training.action', 'Training action'),
            ('academy.training.activity', 'Training activity'),
            ('academy.competency.unit', 'Competency unit'),
            ('academy.training.module', 'Training module')
        ]
    )

    # NEW: this field was added after migration
    training_type = fields.Selection(
        string='Training type',
        required=True,
        readonly=False,
        index=True,
        default=False,
        help='Type of training: Enrolment, Action, Activity,...',
        selection=[
            ('academy.training.action.enrolment', 'Enrolment'),
            ('academy.training.action', 'Training action'),
            ('academy.training.activity', 'Training activity'),
            ('academy.competency.unit', 'Competency unit'),
            ('academy.training.module', 'Training module')
        ]
    )

    # NEW: this field was added after migration
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

    # NEW: this field was added after migration
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

    # NEW: this field was added after migration
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

    # NEW: this field was added after migration
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

    # NEW: this field was added after migration
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

    # ----------------- AUXILIARY FIELDS METHODS AND EVENTS -------------------
