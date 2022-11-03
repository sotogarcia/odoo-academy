# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _

from logging import getLogger
from datetime import datetime, timedelta

_logger = getLogger(__name__)


class CivilServiceRecruitmentProcess(models.Model):
    """ All information about the public examination process
    """

    _name = 'civil.service.recruitment.process'
    _description = u'Civil service recruitment'

    _inherit = [
        'image.mixin',
        'ownership.mixin',
        'mail.thread',
        'mail.activity.mixin'
    ]

    _rec_name = 'name'
    _order = 'name ASC'

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

    name = fields.Char(
        string='Denomination',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Name for this civil service recruitment',
        size=255,
        translate=True,
        tracking=True
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this civil service recruitment',
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
        tracking=True
    )

    offer_id = fields.Many2one(
        string='Public offer',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose the related public offer',
        comodel_name='civil.service.recruitment.public.offer',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    group_id = fields.Many2one(
        string='Group',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self._default_employment_group_id(),
        help='Choose employment group for this selection process',
        comodel_name='civil.service.recruitment.employment.group',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    corps_id = fields.Many2one(
        string='Corps',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='civil.service.recruitment.public.corps',
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
        help='Choose type of exam for this selection process',
        comodel_name='civil.service.recruitment.exam.type',
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
        help='Choose hiring type for this selection process',
        comodel_name='civil.service.recruitment.hiring.type',
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
        help='Choose access system for this selection process',
        comodel_name='civil.service.recruitment.access.system',
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
        tracking=True,
        compute=lambda self: self._compute_state_date('approval')
    )

    announcement = fields.Date(
        string='Announcement date',
        required=False,
        readonly=True,
        index=False,
        default=fields.Date.today(),
        help='Choose the Announcement date',
        tracking=True,
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
        help='Choose the due date for selection process',
        tracking=True
    )

    vacancy_ids = fields.One2many(
        string='Vacancies',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Add offered selection process',
        comodel_name='civil.service.recruitment.vacancy.position',
        inverse_name='process_id',
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
        help='Documents related with the civil service recruitment',
        comodel_name='ir.attachment',
        relation='civil_service_recruitment_process_ir_attachment_rel',
        column1='process_id',
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
        string='Vacancy count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        compute='compute_total_of_vacancies',
        help='Set number of vacancies'
    )

    state_id = fields.Many2one(
        string='State',
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self._default_state_id(),
        help='Show last event type',
        comodel_name='civil.service.recruitment.event.type',
        domain=[('stage_id', '=', True)],
        context={},
        ondelete='cascade',
        auto_join=False,
        group_expand='_read_group_state_ids',
        store=True,
        tracking=True
    )

    event_ids = fields.One2many(
        string='Events',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Register new related events',
        comodel_name='civil.service.recruitment.event',
        inverse_name='process_id',
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
        comodel_name='civil.service.recruitment.event',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        compute=lambda self: self._compute_last_event_id()
    )

    _sql_constraints = [
        (
            'unique_name',
            'UNIQUE("name")',
            _('Another record with the same name already exists')
        )
    ]

    def _track_subtype(self, init_values):
        xid = 'civil_service_recruitment.civil_service_recruitment_state_change'

        self.ensure_one()

        if('state_id' in init_values.keys()):
            return self.env.ref(xid).copy()

        _super = super(CivilServiceRecruitmentProcess, self)
        return _super._track_subtype(init_values)

    # ----------------------- AUXILIAR FIELD METHODS --------------------------

    @api.onchange('event_ids')
    def _onchange_public_process_event_ids(self):
        for record in self:
            record._compute_state_date('approval')
            record._compute_state_date('announcement')
            record._compute_state_date('finished')
            record._compute_last_event_id()
            record._ensure_state_id()

    @api.onchange('group_id')
    def _onchange_employment_group_id(self):
        _id = self.group_id.id or -1
        return {
            'domain': {
                'corps_id': [('group_id', '=', _id)]
            }
        }

    @api.model
    def _default_employment_group_id(self):
        """ Returns the default value for group_id field.
        """

        xid = ('civil_service_recruitment.'
               'civil_service_recruitment_employment_group_c1')
        record = self.env.ref(xid)

        return record.id

    @api.model
    def _default_exam_type_id(self):
        """ Returns the default value for kind_id field.
        """

        xid = ('civil_service_recruitment.'
               'civil_service_recruitment_exam_type_exam')
        record = self.env.ref(xid)

        return record.id

    @api.model
    def _default_hiring_type_id(self):
        """ Returns the default value for class_id field.
        """

        xid = ('civil_service_recruitment.'
               'civil_service_recruitment_hiring_type_career')
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

    @api.depends('vacancy_ids')
    def compute_total_of_vacancies(self):
        """ Returns computed value for total_of_vacancies field
        """
        for record in self:
            record.total_of_vacancies = \
                sum(record.vacancy_ids.mapped('quantity'))

    def _default_state_id(self):
        """ Returns the state with lowerest sequence
        @note: Some event_types are used as the states
        """

        order = 'sequence ASC'
        event_type_domain = [('is_stage', '=', True)]
        event_type_obj = self.env['civil.service.recruitment.event.type']
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

            if record.event_ids:

                # STEP 1: Search for field with given name
                field_domain = [
                    ('name', '=', field_name),
                    ('model', '=', record._name)
                ]
                field_obj = record.env['ir.model.fields']
                field_set = field_obj.search(field_domain)

                # STEP 2: Seach for event type related with this field
                etype_domain = [('related_field_id', '=', field_set.id)]
                etype_obj = record.env['civil.service.recruitment.event.type']
                etype_set = etype_obj.search(etype_domain, limit=1)

                # STEP 3: Search for events of this type in this proccess
                if etype_set:
                    event_set = record.event_ids.filtered(
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
            etype_obj = record.env['civil.service.recruitment.event.type']
            etype_set = etype_obj.search(etype_domain, limit=1)

            # STEP 3: Search for events of this type in this proccess
            if etype_set:
                event_set = record.event_ids.filtered(
                    lambda x: x.event_type_id.id == etype_set.id)

                if event_set:
                    pass
                    event_set.date = in_date
                else:
                    pass
                    event_set.create([{
                        'date': in_date,
                        'event_type_id': etype_set.id,
                        'process_id': record.id,
                    }])

            record.touch()

    @api.depends('event_ids')
    def _compute_last_event_id(self):
        for record in self:
            sorted_set = record.event_ids.sorted('date', True)
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
            event_type_set = record.event_ids.mapped(
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

        _super = super(CivilServiceRecruitmentProcess, self)
        result = _super.create(values)

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

        _super = super(CivilServiceRecruitmentProcess, self)
        result = _super.write(values)

        if 'state_id' not in values:
            self._ensure_state_id()

        return result

    @api.model
    def _read_group_state_ids(self, stages, domain, order):
        """ Ensure all available states are shown in kanvan view
        @note: Some event_types are used as the states
        """
        event_type_domain = [('is_stage', '=', True)]
        event_type_obj = self.env['civil.service.recruitment.event.type']
        event_type_set = event_type_obj.search(
            event_type_domain, order="sequence ASC")

        return event_type_set
