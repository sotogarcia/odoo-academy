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


class AcademyTrainingInvitation(models.Model):
    """ Invitation to participate in a training session for a student
    """

    _name = 'academy.training.session.invitation'
    _description = u'academy training session invitation'

    _rec_name = 'id'
    _order = 'write_date DESC'

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

    state = fields.Selection(
        string='State',
        readonly=True,
        help='Current session status',
        related='session_id.state'
    )

    session_id = fields.Many2one(
        string='Session',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Related training session',
        comodel_name='academy.training.session',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    @api.onchange('session_id')
    def _onchange_session_id(self):
        self.present = False

    date_start = fields.Datetime(
        string='Beginning',
        readonly='True',
        help='Date/time of session start',
        related='session_id.date_start'
    )

    date_stop = fields.Datetime(
        string='Ending',
        readonly='True',
        help='Date/time of session end',
        related='session_id.date_stop'
    )

    date_delay = fields.Float(
        string='Duration',
        readonly='True',
        help='Time length of the training session',
        related='session_id.date_delay'
    )

    manager_id = fields.Many2one(
        string='Manager',
        readonly=True,
        related='session_id.manager_id'
    )

    exclusion_ids = fields.One2many(
        string='Exclusions',
        help='List with studentswho have not been invited',
        related='session_id.exclusion_ids'
    )

    training_action_id = fields.Many2one(
        string='Training action',
        help='Related training action',
        related='session_id.training_action_id'
    )

    competency_unit_id = fields.Many2one(
        string='Competency unit',
        readonly='True',
        help='Related competency unit',
        related='session_id.competency_unit_id'
    )

    primary_teacher_id = fields.Many2one(
        string='Primary instructor',
        readonly='True',
        help='Teacher with primary responsibility',
        related='session_id.primary_teacher_id'
    )

    primary_facility_id = fields.Many2one(
        string='Primary facility',
        help='Main facility where the training session will take place',
        related='session_id.primary_facility_id'
    )

    invitation_ids = fields.One2many(
        string='Other invitations',
        help='List of attendees for the session',
        related='session_id.invitation_ids'
    )

    enrolment_id = fields.Many2one(
        string='Enrolment',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Related training action enrolment',
        comodel_name='academy.training.action.enrolment',
        domain=lambda self: self._enrolment_domain('overlapped'),
        context={},
        ondelete='cascade',
        auto_join=False
    )

    student_id = fields.Many2one(
        string='Student',
        readonly=True,
        related='enrolment_id.student_id',
        store=True
    )

    vat = fields.Char(
        string='Tax ID',
        readonly='True',
        related='student_id.vat'
    )

    zip = fields.Char(
        string='Zip',
        readonly='True',
        related='student_id.zip'
    )

    mobile = fields.Char(
        string='Mobile',
        readonly='True',
        related='student_id.mobile'
    )

    email = fields.Char(
        string='Email',
        readonly='True',
        related='student_id.email'
    )

    image_1920 = fields.Image(
        string='Image',
        related='student_id.image_1920'
    )

    image_1024 = fields.Image(
        string='Image 1024',
        related='student_id.image_1024'
    )

    image_512 = fields.Image(
        string='Image 512',
        related='student_id.image_512'
    )

    image_256 = fields.Image(
        string='Image 256',
        related='student_id.image_256'
    )

    image_128 = fields.Image(
        string='Image 128',
        related='student_id.image_128'
    )

    present = fields.Boolean(
        string='Present',
        required=False,
        readonly=False,
        index=True,
        default=False,
        help='Check it only if the student is present'
    )

    _sql_constraints = [
        (
            'unique_enrolment_by_session',
            'UNIQUE(session_id, enrolment_id)',
            _(u'The enrolment has already been used in this session')
        ),
        (
            'unique_student_by_session',
            'UNIQUE(session_id, student_id)',
            _(u'The student has already been invited to the session')
        )
    ]

    def name_get(self):
        result = []

        default_student_id = self.env.context.get('default_student_id', False)

        for record in self:
            session = record.session_id.display_name or _('New session')

            if default_student_id:
                name = session
            else:
                student = record.student_id.name or _('New student')
                name = '%s - %s' % (session, student)

            result.append((record.id, name))

        return result

    @staticmethod
    def _enrolment_domain(case):
        """ Check if affinity ovelaps with its own session date range

        First I computed the domain for those outside, then I computed negating
        it the overlap domain. To do this, I applied the Laws of Morgan.

                       R                  D
                       ├──────────────────┤···

        ╟─────╢    ╟─────╢    ╟─────╢    ╟─────╢    ╟─────╢
          OUT        IN         IN         IN         OUT
                     ╟──────────────────────╢
        """

        if case == 'in':
            domain = '''[
                "&",
                ("register", "<=", date_start),
                "|",
                ("deregister", "=", False),
                ("deregister", ">=", date_stop)
            ]'''

        elif case == 'out':
            domain = '''[
                "|",
                ("register", ">=", date_stop),
                "&",
                ("deregister", "<>", False),
                ("deregister", "<=", date_start)
            ]'''

        elif case == 'overlapped':
            domain = '''[
                "&",
                ("register", "<", date_stop),
                "|",
                ("deregister", "=", False),
                ("deregister", ">", date_start)
            ]'''

        else:
            raise UserError('Invalid ``case`` passed to ``_enrolment_domain``')

        return domain
