# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError

from logging import getLogger
from datetime import timedelta
from base64 import encodebytes

_logger = getLogger(__name__)


class AcademyTimesheetsSendByMailWizard(models.TransientModel):
    """
    """

    _name = 'academy.timesheets.send.by.mail.wizard'
    _description = u'Academy timesheets send by mail'

    _rec_name = 'id'
    _order = 'id DESC'

    active_model = fields.Selection(
        string='Active model',
        required=False,
        readonly=True,
        index=True,
        default=lambda self: self.default_active_model(),
        help='Target model',
        selection=[
            ('academy.training.action', 'Training action'),
            ('academy.training.session', 'Training session'),
            ('academy.training.session.invitation', 'Session invitation'),
            ('academy.student', 'Student'),
            ('academy.teacher', 'Teacher'),
        ]
    )

    def default_active_model(self):
        return self.env.context.get('active_model', None)

    target_count = fields.Integer(
        string='Selected items',
        required=True,
        readonly=True,
        index=True,
        default=lambda self: self.default_target_count(),
        help='Number of emails will be sent'
    )

    def default_target_count(self):
        return len(self._get_active_ids())

    date_start = fields.Datetime(
        string='Beginning',
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self.week_start(),
        help='Date/time of session start'
    )

    @api.onchange('date_start')
    def _onchange_date_start(self):
        self._correct_dates(stop_changes=False)

    date_stop = fields.Datetime(
        string='Ending',
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self.week_start() + timedelta(days=6),
        help='Date/time of session end'
    )

    @api.onchange('date_stop')
    def _onchange_date_stop(self):
        self._correct_dates(stop_changes=True)

    full_weeks = fields.Boolean(
        string='Full weeks',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Always show full weeks'
    )

    force_send = fields.Boolean(
        string='Force send',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help=('If True, the generated mail will be immediately sent after '
              'being created, as if the scheduler was executed for this '
              'message only')
    )

    def _correct_dates(self, stop_changes=False):
        msg = _('Last date should be later than first date')

        for record in self:
            if record.date_start > record.date_stop:
                if stop_changes:
                    raise ValidationError(msg)
                else:
                    record.date_stop = record.date_start + timedelta(days=1)

    def week_start(self):
        return self.env['facility.reporting.wizard'].week_start()

    def send_by_mail(self):
        """ Send email with a PDF document containing the schedule.

        The email message must be sent to each recipient individually.

        Students and teachers have its own report but the other models share
        the same. Thus, for all these models, the PDF document must be
        generated separately for each associated training action and then
        attached to each of the outgoing emails.

        """
        self.ensure_one()
        self._validate()

        model = self._get_active_model()
        active_ids = self._get_active_ids()

        record_set = self._get_active_records(model, active_ids)

        email_values = {'email_to': None}
        email_template = self._get_email_template(model)
        context = self._compute_report_context()
        email_template = email_template.with_context(context)

        # Report will be empty when the model corresponds to student or teacher
        # In any other case the training action report will be used.
        training_action_report = self._get_training_action_report(model)

        for record in record_set:
            target = self._get_target(record, model)
            recipients = self._get_recipients(record, model)

            if training_action_report:
                self._attach_training_action_report(
                    email_values, training_action_report, target)

            # Emails will be sent to each user individually
            for recipient in recipients:
                email_values.update({'email_to': recipient})
                email_template.send_mail(target.id, email_values=email_values,
                                         force_send=self.force_send)

    def _get_training_action_report(self, model):
        if model not in ['academy.teacher', 'academy.student']:
            report_xid = self._get_report_xid(model)
            self_ctx = self._with_referrer()
            report = self_ctx.env.ref(report_xid)
        else:
            report = self.env['ir.actions.report']

        return report

    def _render_training_action_report(self, report, training_action):

        datas = {
            'doc_ids': [training_action.id],
            'doc_model': 'academy.training.action',
            'interval': self.read(['date_start', 'date_stop'])[0],
            'full_weeks': self.full_weeks
        }

        content, c_type = report.render_qweb_pdf(
            [training_action.id], data=datas)

        attachment = self.env['ir.attachment'].create({
            'name': training_action.display_name,
            'type': 'binary',
            'datas': encodebytes(content),
            'res_model': 'academy.training.action',
            'res_id': training_action.id
        })

        return attachment

    def _attach_training_action_report(self, email_values, report, action):
        attachment = self._render_training_action_report(report, action)
        m2m_ops = [(5, 0, 0), (4, attachment.id, 0)]
        email_values.update({'attachment_ids': m2m_ops})

    def _with_referrer(self):
        """ Update context to communicate that the referrer will be this wizard

        Returns:
            Model: ``self`` with the updated context
        """
        ctx = self.env.context.copy()

        ctx.update({
            'active_model': self._name,
            'active_id': self.id,
            'active_ids': []
        })

        return self.with_context(ctx)

    def _validate(self):
        self.ensure_one()

        if self.date_stop < self.date_start:
            msg = _('The interval cannot end without having started')
            raise ValidationError(msg)

    def _get_active_ids(self):
        context = self.env.context

        active_ids = context.get('active_ids', [])
        if not active_ids:
            active_id = context.get('active_id', False)
            if active_id:
                active_ids.append('active_id')

        return active_ids

    def _get_active_model(self):
        return self.env.context.get('active_model', False)

    def _get_active_records(self, model, active_ids):
        domain = [('id', 'in', active_ids)]
        record_obj = self.env[model]
        return record_obj.search(domain)

    @staticmethod
    def _get_report_xid(model):
        if model == 'academy.teacher':
            name = 'action_report_academy_timesheets_primary_instructor'
        elif model == 'academy.student':
            name = 'action_report_academy_timesheets_student'
        else:
            name = 'action_report_academy_timesheets_training_action'

        return '{module}.{name}'.format(module='academy_timesheets', name=name)

    def _get_email_template(self, model):
        if model == 'academy.teacher':
            name = 'mail_template_teacher_schedule'
        elif model == 'academy.student':
            name = 'mail_template_student_schedule'
        else:
            name = 'mail_template_group_schedule'

        template_xid = '{}.{}'.format('academy_timesheets', name)

        return self.env.ref(template_xid)

    def _compute_report_context(self):
        self.ensure_one()

        context = self.env.context.copy()

        context.update({
            'time_span': {
                'date_start': self.date_start.strftime('%Y-%m-%d'),
                'date_stop': self.date_stop.strftime('%Y-%m-%d'),
            },
            'full_weeks': self.full_weeks
        })

        return context

    @staticmethod
    def _get_target(record, model):
        if model == 'academy.training.session':
            target = record.mapped('training_action_id')
        elif model == 'academy.training.session.invitation':
            target = record.mapped('session_id.training_action_id')
        else:
            target = record

        return target

    @staticmethod
    def _get_recipients(record, model):
        student_set = record.env['academy.student']
        teacher_set = record.env['academy.teacher']

        if model == 'academy.training.action':
            student_set = record.mapped(
                'training_action_enrolment_ids.student_id')
            teacher_set = record.mapped('owner_id')

        elif model == 'academy.training.session':
            student_set = record.mapped('inviation_ids.student_id')
            teacher_set = record.mapped('teacher_assignment_ids.teacher_id')

        elif model == 'academy.training.session.invitation':
            student_set = record.mapped('student_id')

        elif model == 'academy.student':
            student_set = record

        elif model == 'academy.teacher':
            teacher_set = record

        recipients = []
        pattern = '{name} <{email}>'
        for student in student_set:
            address = pattern.format(name=student.name, email=student.email)
            recipients.append(address)

        for teacher in teacher_set:
            address = pattern.format(name=teacher.name, email=teacher.email)
            recipients.append(address)

        return recipients
