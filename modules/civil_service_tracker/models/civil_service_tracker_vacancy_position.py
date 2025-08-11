# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)


class CivilServiceTrackerVacancyPosition(models.Model):
    """
    Represents a specific type of position within a civil service
    selection process.

    Each record links a vacancy type to a selection process, defining
    how many positions of that type are offered. Threads of messages
    are transferred to the parent selection process upon creation
    or update to centralize communication.
    """

    _name = 'civil.service.tracker.vacancy.position'
    _description = u'Civil service tracker vacancy position'

    _table = 'cst_vacancy_position'

    _rec_name = 'name'
    _order = 'name ASC'

    _inherit = ['civil.service.tracker.thread.to.parent.mixin']

    name = fields.Char(
        string='Position name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Name of the position offered (e.g. Administrative Assistant)',
        translate=True,
        track_visibility='always'
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Additional information about this position (optional)',
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=True,
        default=True,
        help='Enable or disable this vacancy position without deleting it',
        track_visibility='onchange'
    )

    sequence = fields.Integer(
        string='Sequence',
        required=True,
        readonly=False,
        index=True,
        default=1,
        help='Controls display order in the selection process',
        track_visibility='onchange'
    )

    vacancy_type_id = fields.Many2one(
        string='Vacancy type',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Position category (e.g. Free Turn, Promotion)',
        comodel_name='civil.service.tracker.vacancy.type',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        track_visibility='onchange'
    )

    @api.onchange('vacancy_type_id')
    def _onchange_vacancy_type_id(self):
        if not self.vacancy_type_id:
            return

        new_name = self.vacancy_type_id.name
        current_name = self.name or ''
        previous_name = self._origin.name if self._origin else ''

        # Si es nuevo (sin origen) y el nombre está vacío → asignar el nuevo.
        if not self._origin and not current_name:
            self.name = new_name

        # Si ya existía y no ha sido editado manualmente → asignar el nuevo.
        elif current_name == previous_name and current_name != new_name:
            self.name = new_name

    position_quantity = fields.Integer(
        string='Number of positions',
        required=True,
        readonly=False,
        index=True,
        default=0,
        help='Total number of positions available for this type',
        track_visibility='always'
    )

    selection_process_id = fields.Many2one(
        string='Selection process',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Selection process to which this vacancy position is linked',
        comodel_name='civil.service.tracker.selection.process',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        track_visibility='onchange'
    )

    # -------------------------------------------------------------------------
    # CONSTRAINTS
    # -------------------------------------------------------------------------

    _sql_constraints = [
        (
            'unique_vacancy_name_per_process',
            'UNIQUE(selection_process_id, name)',
            'Vacancy name must be unique per selection process.'
        ),
        (
            'check_name_min_length',
            'CHECK(char_length(name) > 3)',
            'The name must have more than 3 characters.'
        ),
        (
            'check_positive_quantity',
            'CHECK(position_quantity > 0)',
            'The number of positions must be greater than zero.'
        )
    ]

    # -------------------------------------------------------------------------
    # OVERRIDDEN METHODS
    # -------------------------------------------------------------------------
    
    def _get_tracking_parent(self):
        """
        Returns the record that will act as the parent thread for chatter 
        messages.

        This method is used by the `civil.service.tracker.thread.to.parent.mixin` 
        mixin to redirect messages from this model (typically a child record) 
        to its logical parent, ensuring that all chatter activity is 
        centralized.

        In this case, messages posted on process events will appear in the 
        thread of the linked selection process (`selection_process_id`), 
        providing a unified communication log.

        Returns:
            models.Model: The record to which the chatter thread should be 
            linked.
        """
        return self.selection_process_id

    def _get_tracking_prefix(self):
        return _('Vacancies')

