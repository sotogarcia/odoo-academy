# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import AccessDenied

from logging import getLogger
from datetime import datetime, timedelta

_logger = getLogger(__name__)


class AptPublicTendering(models.Model):
    """ Public tendering information

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.public.tendering.process'
    _description = u'Public tendering'

    _inherit = [
        'image.mixin',
        'mail.thread',
        'academy.abstract.owner'
    ]

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Denomination',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Name for this academy public tendering',
        size=255,
        translate=True,
        track_visibility='always'
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this academy public tendering',
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help=('If the active field is set to false, it will allow you '
              'to hide record without removing it.'),
        track_visibility='onchange'
    )

    public_offer_id = fields.Many2one(
        string='Public offer',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose the related tendering public offer',
        comodel_name='academy.public.tendering.public.offer',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    employment_group_id = fields.Many2one(
        string='Group',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self._default_employment_group_id(),
        help='Choose employment group for this tendering process',
        comodel_name='academy.public.tendering.employment.group',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    public_corps_id = fields.Many2one(
        string='Corps',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.public.tendering.corps',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    exam_type_id = fields.Many2one(
        string='Exam type',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self._default_exam_type_id(),
        help='Choose type of exam for this tendering process',
        comodel_name='academy.public.tendering.exam.type',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
    )

    hiring_type_id = fields.Many2one(
        string='Hiring type',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self._default_hiring_type_id(),
        help='Choose hiring type for this tendering process',
        comodel_name='academy.public.tendering.hiring.type',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
    )

    access_system_id = fields.Many2one(
        string='Access system',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose access system for this tendering process',
        comodel_name='academy.public.tendering.access.system',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    approval = fields.Date(
        string='Approval date',
        required=False,
        readonly=True,
        index=False,
        default=fields.Date.today(),
        help='Choose the approval date',
        track_visibility='onchange',
        compute=lambda self: self._compute_state_date('approval')
    )

    announcement = fields.Date(
        string='Announcement date',
        required=False,
        readonly=True,
        index=False,
        default=fields.Date.today(),
        help='Choose the Announcement date',
        track_visibility='onchange',
        compute=lambda self: self._compute_state_date('announcement')
    )

    finished = fields.Date(
        string='Finished',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Choose date in which process has finished',
        compute=lambda self: self._compute_state_date('finished')
    )

    target_date = fields.Date(
        string='Due date',
        required=False,
        readonly=False,
        index=False,
        # default=lambda self: self.default_submissions_deadline(),
        help='Choose the due date for tendering proccess',
        track_visibility='onchange'
    )

    vacancy_position_ids = fields.One2many(
        string='Vacancy positions',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Add offered tendering process',
        comodel_name='academy.public.tendering.vacancy.position',
        inverse_name='academy_public_tendering_process_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    ir_attachment_ids = fields.Many2many(
        string='Attachments',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Documents related with the academy public tendering',
        comodel_name='ir.attachment',
        relation='academy_public_tendering_process_ir_attachment_rel',
        column1='tendering_process_id',
        column2='ir_atachment_id',
        domain=[],
        context={},
        limit=None
    )

    bulletin_board_url = fields.Char(
        string='Bulletin Board',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='URL of the bulletin board',
        size=256,
        translate=True
    )

    official_journal_url = fields.Char(
        string='Official journal',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='URL of the article in the official journal',
        size=256,
        translate=True
    )

    total_of_vacancies = fields.Integer(
        string='Vacancies',
        required=False,
        readonly=True,
        index=False,
        default=0,
        compute='compute_total_of_vacancies',
        help='Set number of vacancies'
    )

    training_action_ids = fields.Many2many(
        string='Training action',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.training.action',
        relation='academy_training_action_public_tendering_process_rel',
        column1='public_tendering_id',
        column2='training_action_id',
        domain=[],
        context={},
        limit=None,
        track_visibility='onchange'
    )

    training_action_id = fields.Many2one(
        string='Default training action',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Choose the default training action for public tendering',
        comodel_name='academy.training.action',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    state_id = fields.Many2one(
        string='State',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self._default_state_id(),
        help='Show last event type',
        comodel_name='academy.public.tendering.event.type',
        domain=[('stage_id', '=', True)],
        context={},
        ondelete='cascade',
        auto_join=False,
        group_expand='_read_group_state_ids',
        store=True,
        track_visibility='onchange'
    )

    public_process_event_ids = fields.One2many(
        string='Events',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Register new related events',
        comodel_name='academy.public.tendering.event',
        inverse_name='academy_public_tendering_process_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    last_event_id = fields.Many2one(
        string='Last event',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.public.tendering.event',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        compute=lambda self: self._compute_last_event_id()
    )

    def _track_subtype(self, init_values):
        xid = 'academy_public_tendering.academy_public_tendering_state_change'

        self.ensure_one()

        if('state_id' in init_values.keys()):
            return self.env.ref(xid).copy()

        return super(AptPublicTendering, self)._track_subtype(init_values)

    # ----------------------- AUXILIAR FIELD METHODS --------------------------

    @api.onchange('public_process_event_ids')
    def _onchange_public_process_event_ids(self):
        for record in self:
            record._compute_state_date('approval')
            record._compute_state_date('announcement')
            record._compute_state_date('finished')
            record._compute_last_event_id()
            record._ensure_state_id()

    @api.onchange('employment_group_id')
    def _onchange_employment_group_id(self):
        _id = self.employment_group_id.id or -1
        return {
            'domain': {
                'public_corps_id': [('employment_group_id', '=', _id)]
            }
        }

    @api.model
    def _default_employment_group_id(self):
        """ Returns the default value for group_id field.
        """

        xid = ('academy_public_tendering.'
               'academy_public_tendering_employment_group_c1')
        record = self.env.ref(xid)

        return record.id

    @api.model
    def _default_exam_type_id(self):
        """ Returns the default value for kind_id field.
        """

        xid = ('academy_public_tendering.'
               'academy_public_tendering_exam_type_exam')
        record = self.env.ref(xid)

        return record.id

    @api.model
    def _default_hiring_type_id(self):
        """ Returns the default value for class_id field.
        """

        xid = ('academy_public_tendering.'
               'academy_public_tendering_hiring_type_career')
        record = self.env.ref(xid)

        return record

    @staticmethod
    def default_submissions_deadline():
        """ Returns the default value for deadline_for_submissions field. This
        must be twenty days after the announcement date.
        """
        return fields.Date.to_string(
            datetime.now() + timedelta(days=20)
        )

    @api.depends('vacancy_position_ids')
    def compute_total_of_vacancies(self):
        """ Returns computed value for total_of_vacancies field
        """
        for record in self:
            record.total_of_vacancies = \
                sum(record.vacancy_position_ids.mapped('quantity'))

    def _default_state_id(self):
        """ Returns the state with lowerest sequence
        @note: Some event_types are used as the states
        """

        order = 'sequence ASC'
        event_type_domain = [('is_stage', '=', True)]
        event_type_obj = self.env['academy.public.tendering.event.type']
        event_type_set = event_type_obj.search(
            event_type_domain, order=order, limit=1)

        return event_type_set.mapped('id')[0] if event_type_set else None

    def _compute_state_date(self, field_name):
        """ Some date fields in this model must be computed each time of events
        are modified. This method works for all date computed fields in this
        model and, in order to do that, the name of the field will be updated
        must be given on method calling.

        @note: this method do not require @api.depends

        @field_name: name of the field will be updated
        """

        for record in self:
            computed_date = False

            if record.public_process_event_ids:

                # STEP 1: Search for field with given name
                field_domain = [
                    ('name', '=', field_name),
                    ('model', '=', record._name)
                ]
                field_obj = record.env['ir.model.fields']
                field_set = field_obj.search(field_domain)

                # STEP 2: Seach for event type related with this field
                etype_domain = [('related_field_id', '=', field_set.id)]
                etype_obj = record.env['academy.public.tendering.event.type']
                etype_set = etype_obj.search(etype_domain, limit=1)

                # STEP 3: Search for events of this type in this proccess
                if etype_set:
                    event_set = record.public_process_event_ids.filtered(
                        lambda x: x.event_type_id.id == etype_set.id)

                    if event_set:
                        computed_date = max(event_set.mapped('date'))

            setattr(record, field_name, computed_date)

    def _register_event_for_date(self, field_name, in_date):
        """ Some date fields in this model must be computed each time of events
        are modified. This method searches for date field related event to
        update its event date, if the event do not exists then it will be
        created

        @field_name: name of the field will be updated
        """

        for record in self:
            # STEP 1: Search for field with given name
            field_domain = [
                ('name', '=', field_name),
                ('model', '=', record._name)
            ]
            field_obj = record.env['ir.model.fields']
            field_set = field_obj.search(field_domain)

            # STEP 2: Seach for event type related with this field
            etype_domain = [('related_field_id', '=', field_set.id)]
            etype_obj = record.env['academy.public.tendering.event.type']
            etype_set = etype_obj.search(etype_domain, limit=1)

            # STEP 3: Search for events of this type in this proccess
            if etype_set:
                event_set = record.public_process_event_ids.filtered(
                    lambda x: x.event_type_id.id == etype_set.id)

                if event_set:
                    pass
                    event_set.date = in_date
                else:
                    pass
                    event_set.create([{
                        'date': in_date,
                        'event_type_id': etype_set.id,
                        'academy_public_tendering_process_id': record.id,
                    }])

            record.touch()

    @api.depends('public_process_event_ids')
    def _compute_last_event_id(self):
        for record in self:
            sorted_set = record.public_process_event_ids.sorted('date', True)
            if sorted_set:
                record.last_event_id = sorted_set[0]
            else:
                record.last_event_id = None

    # ------------------------- AUXILIARY  METHODS ----------------------------

    def _ensure_state_id(self):
        """ Recomputes state_id field value using related process events
        This methos should be invoked from create and write methods, as well as
        by the same methods in related events and event types
        """

        for record in self:
            event_type_set = record.public_process_event_ids.mapped(
                'event_type_id')
            event_type_set = event_type_set.filtered(lambda x: x.is_stage)

            if event_type_set:
                record.state_id = event_type_set.sorted('sequence', True)[0]
            else:
                record.state_id = self._default_state_id()

        return self

    # --------------------------- PUBLIC METHODS ------------------------------

    def update_states(self):
        """ This method will be called by the cron server action to keep
        process states. This can update the recordet from method was called or
        selected records in views of all records when recordset from has been
        called it's empty (ir.cron).
        """

        if self:
            process_set = self
        elif self.env.context.get('active_model', None) == self._name:
            ids = self.env.context.get('active_ids', [])
            process_set = self.browse(ids)
        else:
            process_set = self.search([])

        process_set.touch()

    def touch(self):
        """ This method should be called from other models to update related
        records
        """

        for record in self:

            # STEP 1: Set the value of the computed fields
            record._compute_state_date('approval')
            record._compute_state_date('announcement')
            record._compute_state_date('finished')

            # STEP 2: Update non computed fields which depend from others
            record._ensure_state_id()

    def set_approval(self, approval):
        self._register_event_for_date('approval', approval)

    def set_announcement(self, announcement):
        self._register_event_for_date('announcement', announcement)

    # ------------------------- OVERLOADED METHODS ----------------------------

    @api.model
    def create(self, values):
        """ Once record has been created its state is computed and stored
        """

        result = super(AptPublicTendering, self).create(values)

        result._ensure_state_id()

        return result

    def write(self, values):
        """ Once all other values in redordset has been written the state is
        computed for each one of them

        @note: the cost of this operation depends of the number of records
        in the recordset.
        @note: this operation can not be performed over all records at the same
        time becouse each one of them can have a different state value
        """

        result = super(AptPublicTendering, self).write(values)

        if 'state_id' not in values:
            self._ensure_state_id()

        return result

    @api.model
    def _read_group_state_ids(self, stages, domain, order):
        """ Ensure all available states are shown in kanvan view
        @note: Some event_types are used as the states
        """
        event_type_domain = [('is_stage', '=', True)]
        event_type_obj = self.env['academy.public.tendering.event.type']
        event_type_set = event_type_obj.search(
            event_type_domain, order="sequence ASC")

        return event_type_set
