# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _

from logging import getLogger


_logger = getLogger(__name__)


class CivilServiceRecruitmentEventType(models.Model):
    """ Allow to group similar civil service recruitment process events
    """

    _name = 'civil.service.recruitment.event.type'
    _description = u'Civil service recruitment event'

    _rec_name = 'name'
    _order = 'sequence ASC, name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Name for this kind',
        size=255,
        translate=True
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this kind',
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

    sequence = fields.Integer(
        string='Sequence',
        required=False,
        readonly=False,
        index=False,
        default=0,
        help='Choose this event type order position'
    )

    is_stage = fields.Boolean(
        string='Is stage',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help=('Check it this event type is a civil service recruitment process state')
    )

    unique = fields.Boolean(
        string='Unique',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help=('Check it this event type can not be repeated in the '
              'same civil service recruitment')
    )

    fold = fields.Boolean(
        string='Fold',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help='Fold when is used as stage in kanban view'
    )

    related_field_id = fields.Many2one(
        string='Related field',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='ir.model.fields',
        domain=[
            ('model', '=', 'civil.service.recruitment.process'),
            ('ttype', '=', 'date'),
            ('store', '=', False)
        ],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    event_ids = fields.One2many(
        string='Events',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Register new related events',
        comodel_name='civil.service.recruitment.event',
        inverse_name='event_type_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    _sql_constraints = [
        (
            'unique_name',
            'UNIQUE("name")',
            _('Another record with the same name already exists')
        )
    ]

    @api.model
    def create(self, values):
        """ Touches all selection processes to ensure state_id, both those
        which are related and those which are not
        """
        # STEP 0: For backward compatibility, ``vals_list`` may be a dictionary
        values = values if isinstance(values, list) else [values]

        result = super(CivilServiceRecruitmentEventType, self).create(values)

        model = self.env.context.get('model', False)
        if model != 'civil.service.recruitment.process':
            process_obj = self.env['civil.service.recruitment.process']
            process_set = process_obj.search([])
            process_set.touch()

        return result

    # def write(self, values):
    #     """ Touches all selection processes to ensure state_id, both those
    #     which are related and those which are not
    #     """

    #     result = super(CivilServiceRecruitmentEventType, self).write(values)

    #     model = self.env.context.get('model', False)
    #     if model != 'civil.service.recruitment.process':
    #         process_obj = self.env['civil.service.recruitment.process']
    #         process_set = process_obj.search([])
    #         process_set.touch()

    #     return result
