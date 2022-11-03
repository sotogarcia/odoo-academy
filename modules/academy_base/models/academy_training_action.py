# -*- coding: utf-8 -*-
""" AcademyTrainingAction

This module contains the academy.training.action Odoo model which stores
all training action attributes and behavior.
"""

from logging import getLogger

from datetime import datetime, timedelta
from pytz import timezone, utc
from odoo.tools.translate import _
from odoo.exceptions import ValidationError

# pylint: disable=locally-disabled, E0401
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
from odoo.osv.expression import AND

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
        'ownership.mixin',
        'image.mixin',
        'mail.thread',
        'mail.activity.mixin'
    ]

    _inherits = {'academy.training.activity': 'training_activity_id'}

    _check_company_auto = True

    company_id = fields.Many2one(
        string='Company',
        required=True,
        readonly=True,
        index=True,
        default=lambda self: self.env.company,
        help='The company this record belongs to',
        comodel_name='res.company',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    state = fields.Selection(
        string='Status',
        required=True,
        readonly=False,
        index=True,
        default='draft',
        help='Crurrent record state',
        selection=[
            ('draft', 'Draft'),
            ('approve', 'Approved')
        ]
    )

    action_name = fields.Char(
        string='Action name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Enter new name',
        size=1024,
        translate=True,
        tracking=True
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
        help='Start date of an event, without time for full day events',
        tracking=True
    )

    # pylint: disable=locally-disabled, w0212
    end = fields.Datetime(
        string='End',
        required=False,
        readonly=False,
        index=False,
        default=lambda self: self._utc_o_clock(offset=720),
        help='Stop date of an event, without time for full day events',
        tracking=True
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
        limit=None,
        tracking=True
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
        limit=None,
        tracking=True
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
        auto_join=False,
        tracking=True
    )

    action_code = fields.Char(
        string='Internal code',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Enter new internal code',
        size=30,
        translate=False,
        tracking=True
    )

    seating = fields.Integer(
        string='Seating',
        required=False,
        readonly=False,
        index=False,
        default=20,
        help='Maximum number of signups allowed',
        tracking=True
    )

    enrolment_ids = fields.One2many(
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

    student_ids = fields.Many2manyView(
        string='Students',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Show the students have been enrolled in this training action',
        comodel_name='academy.student',
        relation='academy_training_action_enrolment',
        column1='training_action_id',
        column2='student_id',
        domain=[],
        context={},
        limit=None
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

    @api.depends('enrolment_ids')
    def _compute_training_action_enrolment_count(self):
        for record in self:
            record.enrolment_count = \
                len(record.enrolment_ids)

    @api.onchange('enrolment_ids')
    def _onchange_enrolment_ids(self):
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
            'CHECK("start" < "end")',
            _(u'End date must be greater then start date')
        ),
    ]

    @api.constrains('state')
    def _check_state(self):
        message = _('Training action cannot be approved while the training '
                    'activity is in draft status')

        for record in self:
            activity = record.training_activity_id
            if record.state != 'draft' and activity.state == 'draft':
                raise ValidationError(message)

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

    @api.model
    def create(self, values):
        parent = super(AcademyTrainingAction, self)
        result_set = parent.create(values)

        result_set._reconcile_enrolment_state(values)

        return result_set

    def write(self, values):
        parent = super(AcademyTrainingAction, self)
        result = parent.write(values)

        self._reconcile_enrolment_state(values)

        return result

    def _reconcile_enrolment_state(self, values):
        state = values.get('state', False)

        if state == 'draft':
            enrolment_set = self.mapped('enrolment_ids')
            enrolment_set.write({'state': state})

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
