# -*- coding: utf-8 -*-
""" AcademyTrainingAction

This module contains the academy.training.action Odoo model which stores
all training action attributes and behavior.
"""

from logging import getLogger

from datetime import datetime, timedelta
from pytz import timezone, utc
from odoo.tools.translate import _

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
from odoo.osv.expression import AND

from .utils.custom_model_fields import Many2manyThroughView
from .utils.raw_sql import ACADEMY_TRAINING_ACTION_AVAILABLE_RESOURCE_REL, \
    ACADEMY_TRAINING_ACTION_STUDENT_REL

# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903
class AcademyTrainingAction(models.Model):
    """ The training actions represent several groups of students for the same
    training activity
    """

    _name = 'academy.training.action'
    _description = u'Academy training action'

    _rec_name = 'action_name'
    _order = 'action_name ASC'

    _inherit = [
        'image.mixin',
        'mail.thread',
        'academy.abstract.observable',
        'academy.abstract.training',
        'academy.abstract.owner'
    ]

    _inherits = {'academy.training.activity': 'training_activity_id'}

    action_name = fields.Char(
        string='Action name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Enter new name',
        size=1024,
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

    # pylint: disable=locally-disabled, w0212
    start = fields.Datetime(
        string='Start',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self._utc_o_clock(),
        help='Start date of an event, without time for full day events'
    )

    # pylint: disable=locally-disabled, w0212
    end = fields.Datetime(
        string='End',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self._utc_o_clock(offset=720),
        help='Stop date of an event, without time for full day events',
    )

    application_scope_id = fields.Many2one(
        string='Application scope',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.application.scope',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    professional_category_id = fields.Many2one(
        string='Professional category',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose related professional category',
        comodel_name='academy.professional.category',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    training_action_category_id = fields.Many2one(
        string='Training action category',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose related training action',
        comodel_name='academy.training.action',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    knowledge_area_ids = fields.Many2many(
        string='Knowledge areas',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose related knowledge areas',
        comodel_name='academy.knowledge.area',
        relation='academy_training_action_knowledge_area_rel',
        column1='training_action_id',
        column2='knowledge_area_id',
        domain=[],
        context={},
        limit=None
    )

    training_modality_ids = fields.Many2many(
        string='Training modalities',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose training modalities',
        comodel_name='academy.training.modality',
        relation='academy_training_action_training_modality_rel',
        column1='training_action_id',
        column2='training_modality_id',
        domain=[],
        context={},
        limit=None
    )

    training_methodology_ids = fields.Many2many(
        string='Training methodology',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose training methodologies',
        comodel_name='academy.training.methodology',
        relation='academy_training_action_training_methodology_rel',
        column1='training_action_id',
        column2='training_methodology_id',
        domain=[],
        context={},
        limit=None
    )

    training_activity_id = fields.Many2one(
        string='Training activity',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Training activity will be imparted in this action',
        comodel_name='academy.training.activity',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    action_code = fields.Char(
        string='Internal code',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Enter new internal code',
        size=30,
        translate=False
    )

    seating = fields.Integer(
        string='Seating',
        required=False,
        readonly=False,
        index=False,
        default=20,
        help='Maximum number of signups allowed'
    )

    training_action_enrolment_ids = fields.One2many(
        string='Action enrolments',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Show the number of enrolments related with the training action',
        comodel_name='academy.training.action.enrolment',
        inverse_name='training_action_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    action_resource_ids = fields.Many2many(
        string='Action resources',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.resource',
        relation='academy_training_action_training_resource_rel',
        column1='training_action_id',
        column2='training_resource_id',
        domain=[],
        context={},
        limit=None
    )

    available_resource_ids = Many2manyThroughView(
        string='Available action resources',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.resource',
        relation='academy_training_action_available_resource_rel',
        column1='training_action_id',
        column2='training_resource_id',
        domain=[],
        context={},
        limit=None,
        sql=ACADEMY_TRAINING_ACTION_AVAILABLE_RESOURCE_REL
    )

    student_ids = Many2manyThroughView(
        string='Students',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Show the students have been enrolled in this training action',
        comodel_name='academy.student',
        relation='academy_training_action_student_rel',
        column1='training_action_id',
        column2='student_id',
        domain=[],
        context={},
        limit=None,
        sql=ACADEMY_TRAINING_ACTION_STUDENT_REL
    )

    enrolment_count = fields.Integer(
        string='Nº enrolments',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of enrolments',
        compute='_compute_training_action_enrolment_count'
    )

    lesson_ids = fields.One2many(
        string='Lessons',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.lesson',
        inverse_name='training_action_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    lesson_count = fields.Integer(
        string='Nº lessons',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show the number of related lessons',
        compute='_compute_lesson_count'
    )

    @api.depends('lesson_ids')
    def _compute_lesson_count(self):
        for record in self:
            record.lesson_count = len(record.lesson_ids)

    @api.depends('training_action_enrolment_ids')
    def _compute_training_action_enrolment_count(self):
        for record in self:
            record.enrolment_count = \
                len(record.training_action_enrolment_ids)

    @api.onchange('training_action_enrolment_ids')
    def _onchange_training_action_enrolment_ids(self):
        self._compute_training_action_enrolment_count()

    # ------------------------------ CONSTRAINS -------------------------------

    _sql_constraints = [
        (
            'unique_action_code',
            'UNIQUE(action_code)',
            _(u'The given action code already exists')
        ),
        (
            'check_date_order',
            '"start" < "end"',
            _(u'End date must be greater then start date')
        ),
    ]

    # -------------------------- OVERLOADED METHODS ---------------------------

    # @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        """ Prevents new record of the inherited (_inherits) model will be
        created
        """

        default = dict(default or {})
        default.update({
            'training_activity_id': self.training_activity_id.id
        })

        rec = super(AcademyTrainingAction, self).copy(default)
        return rec

    # --------------------------- PUBLIC METHODS ------------------------------

    def session_wizard(self):
        """ Launch the Session wizard.
        This wizard has a related window action, this method reads the action,
        updates context using current evironment and sets the wizard training
        action to this action.
        """

        module = 'academy_base'
        name = 'action_academy_training_session_wizard_act_window'
        act_xid = '{}.{}'.format(module, name)

        self.ensure_one()

        # STEP 1: Initialize variables
        action = self.env.ref(act_xid)
        actx = safe_eval(action.context)

        # STEP 2 Update context:
        ctx = dict()
        ctx.update(self.env.context)    # dictionary from environment
        ctx.update(actx)                # add action context

        # STEP 3: Set training action for wizard. This action will be send in
        # context as a default value. If this recordset have not records,
        # any training action will be set
        if self.id:
            ctx.update(dict(default_training_action_id=self.id))

        # STEP 4: Map training action and add computed context
        action_map = {
            'type': action.type,
            'name': action.name,
            'res_model': action.res_model,
            'view_mode': action.view_mode,
            'target': action.target,
            'domain': action.domain,
            'context': ctx,
            'search_view_id': action.search_view_id,
            'help': action.help,
        }

        # STEP 5: Return the action
        return action_map

    @staticmethod
    def _eval_domain(domain):
        """ Evaluate a domain expresion (str, False, None, list or tuple) an
        returns a valid domain

        Arguments:
            domain {mixed} -- domain expresion

        Returns:
            mixed -- Odoo valid domain. This will be a tuple or list
        """

        if domain in [False, None]:
            domain = []
        elif not isinstance(domain, (list, tuple)):
            try:
                domain = eval(domain)
            except Exception:
                domain = []

        return domain

    def show_training_action_enrolments(self):

        self.ensure_one()

        act_xid = 'academy_base.action_training_action_enrolment_act_window'
        action = self.env.ref(act_xid)

        domain = self._eval_domain(action.domain)
        domain = AND([domain, [('training_action_id', '=', self.id)]])

        action_values = {
            'name': '{} {}'.format(_('Enrolled in'), self.name),
            'type': action.type,
            'help': action.help,
            'domain': domain,
            'context': {'default_training_action_id': self.id},
            'res_model': action.res_model,
            'target': action.target,
            'view_mode': action.view_mode,
            'search_view_id': action.search_view_id.id,
            'target': 'current',
        }

        return action_values

    # -------------------------- AUXILIARY METHODS ----------------------------

    @api.model
    def _utc_o_clock(self, offset=0, dateonly=False):
        """ Returns Odoo valid current date or datetime with offset.
        This method will be used to set default values for date/time fields

        @param offset: offset in hours
        @param dateonly: return only date without time
        """
        ctx = self.env.context
        tz = timezone(ctx.get('tz')) if ctx.get('tz', False) else utc
        ctx_now = datetime.now(tz)
        utc_now = ctx_now.astimezone(utc)
        utc_offset = utc_now + timedelta(hours=offset)

        utc_ock = utc_offset.replace(minute=0, second=0, microsecond=0)

        if dateonly is True:
            result = fields.Date.to_string(utc_ock.date())
        else:
            result = fields.Datetime.to_string(utc_ock)

        return result
