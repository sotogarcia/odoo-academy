# -*- coding: utf-8 -*-
""" AcademyStudent

This module contains the academy.student Odoo model which stores
all student attributes and behavior.
"""

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
from odoo.osv.expression import OR
from odoo.osv.expression import AND, TRUE_DOMAIN, FALSE_DOMAIN
from odoo.addons.phone_validation.tools.phone_validation import phone_format

from ..utils.record_utils import create_domain_for_ids
from ..utils.record_utils import create_domain_for_interval
from ..utils.record_utils import INCLUDE_ARCHIVED_DOMAIN, ARCHIVED_DOMAIN

from logging import getLogger

_logger = getLogger(__name__)


class AcademyStudent(models.Model):
    """ A student is a partner who can be enrolled on training actions
    """

    _name = 'academy.student'
    _description = u'Academy student'

    _inherit = ['mail.thread']
    _inherits = {'res.partner': 'res_partner_id'}

    _order = 'name ASC'

    res_partner_id = fields.Many2one(
        string='Partner',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='res.partner',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    enrolment_ids = fields.One2many(
        string='Student enrolments',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help=('List all the enrollments, including those that are current, '
              'past, and future'),
        comodel_name='academy.training.action.enrolment',
        inverse_name='student_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    enrolment_count = fields.Integer(
        string='Nº enrolments',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show total number of enrolments',
        compute='_compute_enrolment_count',
        search='_search_enrolment_count'
    )

    @api.depends('enrolment_ids')
    def _compute_enrolment_count(self):
        for record in self:
            record.enrolment_count = len(record.enrolment_ids)

    @api.model
    def _search_enrolment_count(self, operator, value):
        sql = '''
            SELECT
                std."id" AS student_id
            FROM
                academy_student AS std
            LEFT JOIN academy_training_action_enrolment AS enrol
                ON enrol.student_id = std."id"
                AND enrol.company_id IN ( {companies} )
                AND enrol.active
            GROUP BY
                std."id"
            HAVING
                COUNT ( enrol."id" ) {operator} {value}
        '''

        if value == '=' and value is True or value != '=' and value is False:
            return TRUE_DOMAIN

        if value != '=' and value is True or value == '=' and value is False:
            return FALSE_DOMAIN

        training_action_obj = self.env['academy.training.action']
        companies = training_action_obj.join_allowed_companies()

        sql = sql.format(companies=companies, operator=operator, value=value)
        cursor = self.env.cr
        cursor.execute(sql)
        results = cursor.dictfetchall()

        if results:
            record_ids = [item['student_id'] for item in results]
            return [('id', 'in', record_ids)]

        return FALSE_DOMAIN

    current_enrolment_ids = fields.One2many(
        string='Current enrolments',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help=('List all the enrollments, including those that are current, '
              'past, and future'),
        comodel_name='academy.training.action.enrolment',
        inverse_name='student_id',
        domain=[
            '&',
            ('register', '<=', fields.Datetime.now()),
            '|',
            ('deregister', '=', False),
            ('deregister', '>', fields.Datetime.now())
        ],
        context={},
        auto_join=False,
        limit=None
    )

    current_enrolment_count = fields.Integer(
        string='Nº current enrolments',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show total number of enrolments',
        compute='_compute_current_enrolment_count',
        search='_search_current_enrolment_count',
    )

    @api.depends('current_enrolment_ids')
    def _compute_current_enrolment_count(self):
        for record in self:
            record.current_enrolment_count = len(record.current_enrolment_ids)

    @api.model
    def _search_current_enrolment_count(self, operator, value):
        sql = '''
            SELECT
                std."id" AS student_id
            FROM
                academy_student AS std
            LEFT JOIN academy_training_action_enrolment AS enrol
                ON enrol.student_id = std."id" AND
                register <= CURRENT_DATE
                AND (
                    deregister IS NULL
                    OR deregister > CURRENT_DATE
                )
                AND enrol.company_id IN ( {companies} )
                AND enrol.active
            GROUP BY
                std."id"
            HAVING
                COUNT ( enrol."id" ) {operator} {value}
        '''

        if value == '=' and value is True or value != '=' and value is False:
            return TRUE_DOMAIN

        if value != '=' and value is True or value == '=' and value is False:
            return FALSE_DOMAIN

        training_action_obj = self.env['academy.training.action']
        companies = training_action_obj.join_allowed_companies()

        sql = sql.format(companies=companies, operator=operator, value=value)
        cursor = self.env.cr
        cursor.execute(sql)
        results = cursor.dictfetchall()

        if results:
            record_ids = [item['student_id'] for item in results]
            return [('id', 'in', record_ids)]

        return FALSE_DOMAIN

    enrolment_str = fields.Char(
        string='Enrolment str',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Current enrollments over total number of student enrollments',
        size=6,
        translate=False,
        compute='_compute_enrolment_str'
    )

    @api.depends('enrolment_ids', 'current_enrolment_ids', 'enrolment_count',
                 'current_enrolment_count')
    def _compute_enrolment_str(self):
        for record in self:
            current = record.current_enrolment_count or 0
            total = record.enrolment_count or 0

            if total == 0 or current == total:
                record.enrolment_str = str(total)
            else:
                record.enrolment_str = '{} / {}'.format(current, total)

    training_action_ids = fields.Many2many(
        string='Training actions',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=('List the training actions for which the student has active '
              'enrollments'),
        comodel_name='academy.training.action',
        relation='academy_training_action_student_rel',
        column1='student_id',
        column2='training_action_id',
        domain=[],
        context={},
        limit=None,
        copy=False,
        compute='_compute_training_action_ids',
        search='_search_training_action_ids'
    )

    @api.depends('enrolment_ids', 'enrolment_ids.training_action_id')
    def _compute_training_action_ids(self):
        for record in self:
            record.field = self.mapped('enrolment_ids.training_action_id')

    @api.model
    def _search_training_action_ids(self, operator, value):
        return [('enrolment_ids.training_action_id', operator, value)]

    attainment_id = fields.Many2one(
        string='Educational attainment',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Choose related educational attainment',
        comodel_name='academy.educational.attainment',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    birthday = fields.Date(
        string='Birthday',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Date on which the student was born'
    )

    _sql_constraints = [
        (
            'unique_partner',
            'UNIQUE(res_partner_id)',
            _(u'There is already a student for this contact')
        )
    ]

    @api.constrains('res_partner_id')
    def _check_res_partner_id(self):
        partner_obj = self.env['res.partner']
        msg = _('There is already a student with that VAT number or email')

        for record in self:
            if record.res_partner_id:
                leafs = [FALSE_DOMAIN]

                if record.vat:
                    leafs.append([('vat', '=ilike', record.vat)])

                if record.email:
                    leafs.append([('email', '=ilike', record.email)])

                if partner_obj.search_count(OR(leafs)) > 1:
                    raise ValidationError(msg)

    @api.model
    def default_get(self, fields):
        parent = super(AcademyStudent, self)
        values = parent. default_get(fields)

        values['employee'] = False
        values['type'] = 'contact'
        values['is_company'] = False

        return values

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

    def view_enrolments(self):

        self.ensure_one()

        act_xid = 'academy_base.action_training_action_enrolment_act_window'
        action = self.env.ref(act_xid)

        view_xid = ('academy_base.'
                    'view_academy_training_action_enrolment_edit_by_user_tree')

        ctx = self.env.context.copy()
        ctx.update(safe_eval(action.context))
        ctx.update({'default_student_id': self.id})
        ctx.update({'tree_view_ref': view_xid})

        domain = self._eval_domain(action.domain)
        domain = AND([domain, [('student_id', '=', self.id)]])

        action_values = {
            'name': _('Enrolments for «{}»').format(self.name),
            'type': action.type,
            'help': action.help,
            'domain': domain,
            'context': ctx,
            'res_model': action.res_model,
            'target': action.target,
            'view_mode': action.view_mode,
            'search_view_id': action.search_view_id.id,
            'target': 'current',
            'nodestroy': True
        }

        return action_values

    def go_to_contact(self):
        self.ensure_one()

        return {
            'name': self.res_partner_id.name,
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'res.partner',
            'res_id': self.res_partner_id.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'main',
        }

    def sanitize_phone_number(self):
        msg = ('Web scoring calculator: Invalid {} number {}. System says: {}')

        country = self.env.company.country_id
        c_code = country.code if country else None
        c_phone_code = country.phone_code if country else None

        for record in self:
            if record.phone:
                try:
                    phone = phone_format(record.phone, c_code, c_phone_code,
                                         force_format='INTERNATIONAL')
                    record.phone = phone
                except Exception as ex:
                    _logger.debug(msg.format('phone', record.phone, ex))

            if record.mobile:
                try:
                    mobile = phone_format(record.mobile, c_code, c_phone_code,
                                          force_format='INTERNATIONAL')
                    record.mobile = mobile
                except Exception as ex:
                    _logger.debug(msg.format('mobile', record.mobile, ex))

    def fetch_enrolled(self, training_actions=None,
                       point_in_time=None, archived=False):

        student_set = self.env['academy.student']

        domains = []

        if self:
            domain = create_domain_for_ids('student_id', self)
            domains.append(domain)

        if training_actions:
            domain = create_domain_for_ids(
                'training_action_id', training_actions)
            domains.append(domain)

        if point_in_time:
            domain = create_domain_for_interval(
                'register', 'deregister', point_in_time)
            domains.append(domain)

        if archived is None:
            domains.append(INCLUDE_ARCHIVED_DOMAIN)
        elif archived is True:
            domains.append(ARCHIVED_DOMAIN)

        if domains:
            enrolment_obj = self.env['academy.training.action.enrolment']
            enrolment_set = enrolment_obj.search(AND(domains))
            student_set = enrolment_set.mapped('student_id')

        return student_set
