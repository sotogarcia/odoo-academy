# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.addons.academy_base.utils.record_utils import INCLUDE_ARCHIVED_DOMAIN
from odoo.osv.expression import AND
from odoo.exceptions import UserError
from odoo.tools import safe_eval

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTeacher(models.Model):
    """
    """

    _name = 'academy.teacher'
    _inherit = ['academy.teacher']

    employee_id = fields.Many2one(
        string='Employee',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help=('Link to the corresponding HR employee record, enabling unified '
              'management of teacher\'s professional and HR-related data'),
        comodel_name='hr.employee',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    work_location = fields.Char(
        string='Work Location',
        related='employee_id.work_location',
        readonly=False
    )

    work_email = fields.Char(
        string='Work Email',
        related='employee_id.work_email',
        readonly=False
    )

    mobile_phone = fields.Char(
        string='Work Mobile',
        related='employee_id.mobile_phone',
        readonly=False
    )

    work_phone = fields.Char(
        string='Work Phone',
        related='employee_id.work_phone',
        readonly=False
    )

    company_id = fields.Many2one(
        string='Company',
        related='employee_id.company_id'
    )

    department_id = fields.Many2one(
        string='Department',
        related='employee_id.department_id'
    )

    job_id = fields.Many2one(
        string='Job Position',
        related='employee_id.job_id'
    )

    parent_id = fields.Many2one(
        string='Manager',
        related='employee_id.parent_id'
    )

    @api.model
    def _get_current_company(self):
        company_id = self.env.context.get('company_id', False)
        if company_id:
            company_obj = self.env['res.company']
            company = company_obj.browse(company_id)
        else:
            company = self.env.user.company_id

        return company

    def _retrieve_employee_for_user(self, include_archived=False):
        self.ensure_one()

        user_id = self.res_users_id.id

        employee_domain = [('user_id', '=', user_id)]
        if include_archived:
            employee_domain = AND([INCLUDE_ARCHIVED_DOMAIN, employee_domain])

        employee_obj = self.env['hr.employee']
        employee_set = employee_obj.search(employee_domain)

        return employee_set

    @staticmethod
    def _prevent_user_employee_duplication(employee_set):
        log_msg = ('Data inconsistency: One user should not have multiple '
                   'employee records')
        dlg_msg = _('Duplicate Detection: The user is unexpectedly linked to '
                    'several employees')

        if len(employee_set) > 1:
            _logger.error(log_msg)
            raise UserError(dlg_msg)

    @staticmethod
    def _ensure_employee(employee_set, category):
        employee_set.write({
            'active': True,
            'category_ids': [(4, category.id, None)]
        })

    def _new_employee(self, company, department, job, category):
        partner = self.res_users_id.partner_id

        values = {
            'user_id': self.res_users_id.id,
            'active': True,

            'department_id': department.id,
            'job_id': job.id,
            'job_title': _('Teacher'),

            'category_ids': [(4, category.id, None)],
            'address_id': company.partner_id.id,

            'country_id': partner.country_id.id,
            'work_phone': partner.phone,
            'mobile_phone': partner.mobile,
            'work_email': partner.email,
            'work_location': company.name
        }

        employee_obj = self.env['hr.employee']

        return employee_obj.create(values)

    def _convert_teacher_to_employee(self, company, department, job, category):
        self.ensure_one()

        employee = self._retrieve_employee_for_user(include_archived=True)
        if employee:
            self._prevent_user_employee_duplication(employee)
            self._ensure_employee(employee, category)

        else:
            employee = self._new_employee(company, department, job, category)

        self.employee_id = employee

    def convert_teacher_to_employee(self):

        category_xid = ('academy_hr_bridge.'
                        'hr_employee_category_educational_staff')
        category = self.env.ref(category_xid)

        department_xid = 'academy_hr_bridge.hr_department_teaching'
        department = self.env.ref(department_xid)

        job_xid = 'academy_hr_bridge.hr_job_teacher'
        job = self.env.ref(job_xid)

        company = self._get_current_company()

        for record in self:
            record._convert_teacher_to_employee(
                company, department, job, category)

    def view_hr_profile(self):
        self.ensure_one()

        if not self.employee_id:
            message = _('This teacher is not an employee')
            raise UserError(message)

        action_xid = 'hr.open_view_employee_list_my'
        act_wnd = self.env.ref(action_xid)

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))
        context.update({'default_teacher_id': self.id})

        employee_id = self.employee_id.id
        domain = [('id', '=', employee_id)]

        serialized = {
            'type': 'ir.actions.act_window',
            'res_model': act_wnd.res_model,
            'target': 'current',
            'name': act_wnd.display_name,
            'view_mode': act_wnd.view_mode,
            'domain': domain,
            'context': context,
            'search_view_id': act_wnd.search_view_id.id,
            'help': act_wnd.help,
            'res_id': employee_id
        }

        return serialized
