# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields
from odoo.tools import drop_view_if_exists

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTrainingSessionAffinity(models.Model):
    """ This act as middle relation in many to many relationship between
    academy.training.session and academy.student
    """

    _name = 'academy.training.session.affinity'
    _description = u'Academy training session available student'

    _order = 'session_id DESC, student_id DESC'

    _auto = False

    session_id = fields.Many2one(
        string='Session',
        required=True,
        readonly=True,
        index=True,
        default=None,
        help='Related session',
        comodel_name='academy.training.session',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    training_action_id = fields.Many2one(
        string='Training action',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Related training action',
        comodel_name='academy.training.action',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    competency_unit_id = fields.Many2one(
        string='Competency unit',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Related competency unit',
        comodel_name='academy.competency.unit',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    enrolment_id = fields.Many2one(
        string='Enrolment',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Related training action enrolment',
        comodel_name='academy.training.action.enrolment',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    student_id = fields.Many2one(
        string='Student',
        required=True,
        readonly=True,
        index=True,
        default=None,
        help='Related student',
        comodel_name='academy.student',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    invited = fields.Boolean(
        string='Invited',
        required=False,
        readonly=True,
        index=True,
        default=False,
        help='Student has been invited to the session'
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

    def prevent_actions(self):
        actions = ['INSERT', 'UPDATE', 'DELETE']

        BASE_SQL = '''
            CREATE OR REPLACE RULE {table}_{action} AS
                ON {action} TO {table} DO INSTEAD NOTHING
        '''

        for action in actions:
            sql = BASE_SQL.format(table=self._table, action=action)
            self.env.cr.execute(sql)

    def init(self):
        sentence = '''CREATE or REPLACE VIEW {} as ({})'''

        drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute(sentence.format(self._table, self._view_sql))

        self.prevent_actions()

    # Raw sentence used to create new model based on SQL VIEW
    _view_sql = '''
        SELECT
            ROW_NUMBER ( ) OVER ( ) :: INTEGER AS "id",
            GREATEST ( ats.create_uid, enrol.create_uid ) AS create_uid,
            GREATEST ( ats.create_date, enrol.create_date ) AS create_date,
            GREATEST ( ats.write_uid, enrol.write_uid ) AS write_uid,
            GREATEST ( ats.write_date, enrol.write_date ) AS write_date,
            ats."id" AS session_id,
            ats.training_action_id,
            ats.competency_unit_id,
            enrol."id" as enrolment_id,
            enrol.student_id,
            atd."id"::BOOLEAN AS invited
        FROM
            academy_training_session AS ats
        INNER JOIN academy_training_action AS ata
            ON ata.ID = ats.training_action_id
        INNER JOIN academy_competency_unit AS acu
            ON acu.ID = ats.competency_unit_id
        INNER JOIN academy_training_action_enrolment AS enrol
            ON enrol.training_action_id = ata."id"
        INNER JOIN academy_action_enrolment_competency_unit_rel AS rel
            ON rel.action_enrolment_id = enrol."id"
            AND rel.competency_unit_id = acu."id"
        LEFT JOIN academy_training_session_invitation AS atd
            ON atd.enrolment_id = enrol."id"
            AND atd.session_id = ats."id"
        WHERE
            ats.date_start >= enrol.register
            AND ( ats.date_stop <= deregister OR deregister IS NULL )
            AND ata.active
            AND acu.active
            AND enrol.active
    '''

    def name_get(self):
        result = []

        for record in self:
            student = record.student_id.name

            result.append((record.id, student))

        return result

    def toggle_invitation(self):
        invitation_obj = self.env['academy.training.session.invitation']

        for record in self:
            enrolment_id = record.enrolment_id.id
            session_id = record.session_id.id

            if record.invited:
                domain = [
                    ('enrolment_id', '=', enrolment_id),
                    ('session_id', '=', session_id)
                ]
                invitation = invitation_obj.search(domain)
                invitation.unlink()
            else:
                values = {
                    'enrolment_id': enrolment_id,
                    'session_id': session_id,
                    'active': True,
                    'present': False
                }
                invitation_obj.create(values)
