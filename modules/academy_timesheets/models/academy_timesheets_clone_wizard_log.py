# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTimesheetsCloneWizardLog(models.Model):
    """ AcademyTimesheetsCloneWiard logging record
    """

    _name = 'academy.timesheets.clone.wizard.log'
    _description = u'Academy timesheets clone wizard log'

    _rec_name = 'create_date'
    _order = 'wizard_code DESC, sequence DESC, create_date DESC'

    kind = fields.Selection(
        string='Type',
        required=True,
        readonly=True,
        index=True,
        default='ready',
        help='Log type',
        selection=[
            ('50', 'Critical'),
            ('40', 'Error'),
            ('30', 'Warning'),
            ('20', 'Info'),
            ('10', 'Debug'),
            ('00', 'Notset')
        ]
    )

    level = fields.Integer(
        string='Level',
        required=True,
        readonly=True,
        index=True,
        default=0,
        help='Log kind code',
        compute='_compute_level',
        store=True
    )

    @api.depends('kind')
    def _compute_level(self):
        for record in self:
            record.level = int(record.kind) if record.kind else 0

    from_date = fields.Date(
        string='From date',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Date from which the sessions were being copied'
    )

    to_date = fields.Date(
        string='To date',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Date to which the sessions were being copied'
    )

    name = fields.Char(
        string='Name',
        required=True,
        readonly=True,
        index=True,
        default=None,
        help='Short description',
        size=50,
        translate=True
    )

    description = fields.Text(
        string='Description',
        required=True,
        readonly=True,
        index=False,
        default=None,
        help='Long description',
        translate=True
    )

    wizard_code = fields.Integer(
        string='Wizard ID',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help='ID of the wizard which create the log record'
    )

    sequence = fields.Integer(
        string='Sequence',
        required=True,
        readonly=True,
        index=False,
        default=0,
        help='Question sequence order'
    )

    target_ref = fields.Reference(
        string='Target',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Record for which sessions were being copied',
        selection=[
            ('academy.training.action', 'Training action'),
            ('academy.teacher', 'Teacher')
        ]
    )

    session_id = fields.Many2one(
        string='Session',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Session that was being copied',
        comodel_name='academy.training.session',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    def base_values(self, defaults=None):
        base_values = {
            'kind': '20',
            'from_date': None,
            'to_date': None,
            'name': None,
            'description': None,
            'wizard_code': self.id,
            'sequence': 0,
            'target_ref': None,
            'session_id': None
        }

        if isinstance(defaults, dict):
            base_values.update(defaults)

        return base_values

    @api.model
    def _get_target_reference(self, target):
        action_obj = self.env['academy.training.action']
        teacher_obj = self.env['academy.teacher']

        if isinstance(target, type(action_obj)):
            model = 'academy.training.action'
        elif isinstance(target, type(teacher_obj)):
            model = 'academy.teacher'
        else:
            raise UserError(_('The target model is not supported'))

        return '{},{}'.format(model, target.id)

    @api.model
    def _get_target_name(self, target):
        action_obj = self.env['academy.training.action']
        teacher_obj = self.env['academy.teacher']

        if isinstance(target, type(action_obj)):
            name = target.action_name
        elif isinstance(target, type(teacher_obj)):
            name = target.name
        else:
            raise UserError(_('The target model is not supported'))

        return name

    @api.model
    def target(self, sequence, wizard, target):
        name = self._get_target_name(target)
        target_ref = self._get_target_reference(target)
        print(target_ref)
        model, _id = target_ref.split(',')

        msg = _('Change target to «{}». Model: {}, ID: {}')
        msg = msg.format(name, model, _id)

        sequence = sequence + 10
        values = {
            'kind': '10',
            'target_ref': target_ref,
            'wizard_code': wizard.id,
            'name': _('Changing'),
            'description': msg,
            'sequence': sequence
        }

        values = self.base_values(values)
        self.create(values)

        return sequence

    @api.model
    def dates(self, sequence, wizard, target, from_date, to_date):
        msg = _('Change source and target dates to {} and {} respectively')
        msg = msg.format(from_date.strftime('%x'), to_date.strftime('%x'))

        sequence = sequence + 10
        values = {
            'kind': '10',
            'from_date': from_date.strftime('%Y-%m-%d'),
            'to_date': to_date.strftime('%Y-%m-%d'),
            'target_ref': self._get_target_reference(target),
            'wizard_code': wizard.id,
            'name': _('Changing'),
            'description': msg,
            'sequence': sequence
        }

        values = self.base_values(values)
        self.create(values)

        return sequence

    @api.model
    def found(self, sequence, wizard, target, from_date, session):
        name = self._get_target_name(target)

        msg = _('Previous session at {} was found, at {}, for «{}»')
        msg = msg.format(session.date_start.strftime('%X'),
                         from_date.strftime('%x'), name)

        sequence = sequence + 10
        values = {
            'from_date': from_date.strftime('%Y-%m-%d'),
            'target_ref': self._get_target_reference(target),
            'wizard_code': wizard.id,
            'name': _('Searching'),
            'description': msg,
            'sequence': sequence
        }

        values = self.base_values(values)
        self.create(values)

        return sequence

    @api.model
    def delete(self, sequence, wizard, target, from_date):
        name = self._get_target_name(target)

        msg = _('Previously found session, for «{}», with date {} was removed')
        msg = msg.format(name, from_date.strftime('%x'))

        sequence = sequence + 10
        values = {
            'kind': '30',
            'from_date': from_date.strftime('%Y-%m-%d'),
            'target_ref': self._get_target_reference(target),
            'wizard_code': wizard.id,
            'name': _('Removing'),
            'description': msg,
            'sequence': sequence
        }

        values = self.base_values(values)
        self.create(values)

        return sequence

    def no_delete(self, sequence, wizard, target, from_date, session, ex):
        name = self._get_target_name(target)

        msg = _('Previously found session at {}, for «{}», with date {} could'
                ' not be removed. System says: {}')
        msg = msg.format(session.date_start.strftime('%X'), name,
                         from_date.strftime('%x'), ex)

        sequence = sequence + 10
        values = {
            'kind': '40',
            'from_date': from_date.strftime('%Y-%m-%d'),
            'target_ref': self._get_target_reference(target),
            'wizard_code': wizard.id,
            'name': _('Removing'),
            'description': msg,
            'sequence': sequence,
            'session_id': session.id
        }

        values = self.base_values(values)
        self.create(values)

        return sequence

    @api.model
    def clone(self, sequence, wizard, target, from_date, to_date, session):
        name = self._get_target_name(target)

        msg = _('Session at {}, for «{}», with date {} was cloned to {}')
        msg = msg.format(session.date_start.strftime('%X'), name,
                         from_date.strftime('%x'), to_date.strftime('%x'))

        sequence = sequence + 10
        values = {
            'from_date': from_date.strftime('%Y-%m-%d'),
            'to_date': to_date.strftime('%Y-%m-%d'),
            'target_ref': self._get_target_reference(target),
            'wizard_code': wizard.id,
            'name': _('Cloning'),
            'description': msg,
            'sequence': sequence,
            'session_id': session.id
        }

        values = self.base_values(values)
        self.create(values)

        return sequence

    @api.model
    def no_clone(self, seq, wizard, target, from_date, to_date, session, ex):
        name = self._get_target_name(target)

        msg = _('Session at {}, for «{}», with date {} could not be cloned '
                'to {}. System says: {}')
        msg = msg.format(session.date_start.strftime('%X'), name,
                         from_date.strftime('%x'), to_date.strftime('%x'), ex)

        seq = seq + 10
        values = {
            'kind': '40',
            'from_date': from_date.strftime('%Y-%m-%d'),
            'to_date': to_date.strftime('%Y-%m-%d'),
            'target_ref': self._get_target_reference(target),
            'wizard_code': wizard.id,
            'name': _('Cloning'),
            'description': msg,
            'sequence': seq,
            'session_id': session.id
        }

        values = self.base_values(values)
        self.create(values)

        return seq

    @api.model
    def create(self, values):
        """ Ensure level
        """

        values['level'] = int(values['kind'])

        parent = super(AcademyTimesheetsCloneWizardLog, self)
        result = parent.create(values)

        return result

    def write(self, values):
        """ Ensure level
        """

        if 'kind' in values:
            values['level'] = int(values['kind'])

        parent = super(AcademyTimesheetsCloneWizardLog, self)
        result = parent.write(values)

        return result
