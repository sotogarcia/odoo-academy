# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError
from logging import getLogger


_logger = getLogger(__name__)


class AcademyPublicTenderingEvent(models.Model):
    """ The summary line for a class docstring should fit on one line.

    Fields:
      name (Char): Human readable name which will identify each record.

    """

    _name = 'academy.public.tendering.event'
    _description = u'Academy public tendering event'

    _inherit = ['mail.thread']

    _rec_name = 'name'
    _order = 'date ASC, name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Name for this event',
        size=255,
        translate=True
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this event',
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help=('If the active field is set to false, it will allow you '
              'to hide record without removing it.')
    )

    date = fields.Date(
        string='Date',
        required=False,
        readonly=False,
        index=False,
        default=lambda self: fields.Date.context_today(self),
        help='Date the event occurred'
    )

    ir_atachment_id = fields.Many2one(
        string='Attachment',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='The document related with this event',
        comodel_name='ir.attachment',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    event_type_id = fields.Many2one(
        string='Event type',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose a type for this event',
        comodel_name='academy.public.tendering.event.type',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    academy_public_tendering_process_id = fields.Many2one(
        string='Public tendering',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='Choose academy public tendering to which this vacancy belongs',
        comodel_name='academy.public.tendering.process',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    @api.onchange('event_type_id')
    def _onchange_event_type_id(self):
        type_obj = self.env['academy.public.tendering.event.type']
        type_rows = type_obj.search_read([], ['name'])
        types = [item['name'] for item in type_rows]

        if self.event_type_id and (not self.name or self.name in types):
            self.name = self.event_type_id.name

    def _ensure_name(self, value_dict, type_id=False):
        """ If record name field value has not been set this method gets the
        name of the event type to assign it as record name
        """

        if not value_dict.get('name', False):
            type_model = 'academy.public.tendering.event.type'
            type_obj = self.env[type_model]
            type_set = type_obj.browse(type_id)

            value_dict['name'] = type_set.name

        return value_dict

    @api.model
    def create(self, values):
        """ Touches related tendering processes to ensure state_id
        """

        # STEP 0: For backward compatibility, ``vals_list`` may be a dictionary
        values = values if isinstance(values, list) else [values]

        # STEP 1: Use event type name as event name if it has not been set
        for value_dict in values:
            field_name = 'event_type_id'
            type_id = value_dict.get(field_name)
            self._ensure_name(value_dict, type_id)

        # STEP 2: Call parent create method to create record
        result = super(AcademyPublicTenderingEvent, self).create(values)

        # STEP 3: Update state and dates in the related processes
        model = self.env.context.get('model', False)
        if model != 'academy.public.tendering.process':
            result.academy_public_tendering_process_id.touch()

        result.notify_creation()

        return result

    def write(self, values):
        """ Touches related tendering processes to ensure state_id
        """
        # STEP 1: Use event type name as event name if it has not been set
        type_id = self.event_type_id.id
        self._ensure_name(values, type_id)

        # STEP 2: Call parent create method to write record
        result = super(AcademyPublicTenderingEvent, self).write(values)

        # STEP 3: Update state and dates in the related processes
        model = self.env.context.get('model', False)
        if model != 'academy.public.tendering.process':
            self.academy_public_tendering_process_id.touch()

        self.notify_update()

        return result

    def notify_creation(self):
        """ Appends mail message to the parent process notifying new
        related event has been created
        """

        for record in self:
            xid = 'academy_public_tendering_event_created'
            subtype = record.env.ref('academy_public_tendering.' + xid)
            process = record.academy_public_tendering_process_id

            subject = _('Process event created')
            body_format = _('Event «{}» has been registered for process «{}»')
            body = body_format.format(record.name, process.name)
            process.message_post(
                body=body, subject=subject, subtype_id=subtype.id)

    def notify_update(self):
        """ Appends mail message to the parent process notifying existing
        related event has been updated
        """

        for record in self:
            xid = 'academy_public_tendering_event_written'
            subtype = record.env.ref('academy_public_tendering.' + xid)
            process = record.academy_public_tendering_process_id

            subject = _('Process event updated')
            body_format = _('Event «{}» for process «{}» has been updated')
            body = body_format.format(record.name, process.name)
            process.message_post(
                body=body, subject=subject, subtype_id=subtype.id)
