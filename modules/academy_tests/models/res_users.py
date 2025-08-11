# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from logging import getLogger
from collections import defaultdict
from odoo.tools.translate import _

_logger = getLogger(__name__)

UTPL = 'academy_tests.mail_template_uncategorized_questions_by_user_and_topic'
DTPL = 'academy_tests.mail_template_duplicated_questions_by_user_and_topic'
ITPL = 'academy_tests.mail_template_you_have_impugnments'
STPL = 'academy_tests.mail_template_impugnments_summary'


class ResUsers(models.Model):
    """ Extend base.res_users to add a relationship between this model and
    academy.tests.uncategorized.by.user.readonly
    """

    _inherit = 'res.users'

    uncategorized_questions_ids = fields.One2many(
        string='Uncategorized',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Show uncategorized line data',
        comodel_name='academy.tests.uncategorized.by.user.readonly',
        inverse_name='owner_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    duplicate_question_ids = fields.Many2manyView(
        string='Duplicate questions',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Show duplicate questions',
        comodel_name='academy.tests.question',
        relation='academy_res_users_duplicated_questions_rel',
        column1='duplicate_owner_id',
        column2='duplicate_id',
        domain=[],
        context={},
        limit=None,
        copy=False
    )

    duplicate_question_count = fields.Integer(
        string='Number of duplicates',
        required=False,
        readonly=True,
        index=False,
        default=0,
        store=False,
        help='Show number of duplicate questions',
        compute='_compute_duplicate_question_count'
    )

    @api.depends('duplicate_question_ids')
    def _compute_duplicate_question_count(self):
        for record in self:
            record.duplicate_question_count = \
                len(record.duplicate_question_ids)

    @api.onchange('duplicate_question_ids')
    def _onchange_duplicate_question_ids(self):
        self.duplicate_question_count = len(self.duplicate_question_ids)

    @api.model
    def notify_uncategorized(self):
        msg = 'Sending mail to %s notifying uncategorized questions'
        mail_template = self.env.ref(UTPL)
        common_domain = [('provisional', '=', True)]

        category_set = self.env['academy.tests.category']
        category_set = category_set.search(common_domain)
        category_ids = category_set.mapped('id')

        topic_set = self.env['academy.tests.topic']
        topic_set = topic_set.search(common_domain)
        topic_ids = topic_set.mapped('id')

        question_domain = [
            '|',
            ('topic_id', 'in', topic_ids),
            ('category_ids', 'in', category_ids)
        ]
        question_obj = self.env['academy.tests.question']
        question_set = question_obj.search(question_domain)

        manager_set = question_set.mapped('owner_id')

        for user_item in manager_set:
            _logger.info(msg, user_item.name)
            mail_template.send_mail(user_item.id)

    @api.model
    def notify_duplicated(self):
        msg = 'Sending mail to %s notifying  duplicate questions'
        mail_template = self.env.ref(DTPL)
        question_obj = self.env['academy.tests.question']

        question_obj.ensure_checksums()

        domain = [('duplicated_ids', '!=', False)]
        question_set = question_obj.search(domain)

        manager_set = question_set.mapped('owner_id')

        for user_item in manager_set.sorted('name'):
            _logger.info(msg, user_item.name)
            mail_template.send_mail(user_item.id)

    @api.model
    def notify_impugnments(self):
        msg = 'Sending mail to %s notifying impugnments'

        impugnment_domain = [('state', 'in', ['open', 'reply'])]
        impugnment_set = self.env['academy.tests.question.impugnment']
        impugnment_set = impugnment_set.search(impugnment_domain)

        owner_ids = list(set(impugnment_set.mapped('manager_id.id')))

        user_domain = [('id', 'in', owner_ids)]
        user_set = self.env['res.users']
        user_set = user_set.search(user_domain)

        summary_lines = []
        mail_template = self.env.ref(ITPL)
        for user_item in user_set.sorted('name'):
            _logger.info(msg, user_item.name)
            mail_template.send_mail(user_item.id)

            summary_line = self._new_summary_line(impugnment_set, user_item)
            summary_lines.append(summary_line)

        erp_user = self._get_summary_recipient()
        table_html = self._build_summary_table(summary_lines)

        mail_template = self.env.ref(STPL)
        mail_template = mail_template.with_context(table_html=table_html)
        mail_template.send_mail(erp_user.partner_id.id)

        return True

    def _new_summary_line(self, impugnment_set, user_item):

        user_impugnment_set = impugnment_set.filtered(
            lambda i: i.manager_id == user_item
        )
        dates = user_impugnment_set.mapped('create_date')
        dates = list(filter(None, dates))

        if user_item.login_date:
            last_login = fields.Datetime.to_string(user_item.login_date)
        else:
            last_login = _('Never')
            
        return {
            'name': user_item.name,
            'count': len(user_impugnment_set),
            'oldest': fields.Date.to_string(min(dates)) if dates else '',
            'newest': fields.Date.to_string(max(dates)) if dates else '',
            'last_login': last_login
        }

    def _get_summary_recipient(self):
        config = self.env['ir.config_parameter'].sudo()
        param_value = config.get_param('academy_base.erp_manager_id')
        erp_manager_id = self._safe_int(param_value)

        user_obj = self.env['res.users'].sudo()
        erp_user = user_obj.browse(erp_manager_id) if erp_manager_id else None
        
        if not (erp_user and erp_user.id and erp_user.partner_id.email):
            erp_user = self.env.ref('base.user_admin')

        return erp_user

    def _build_summary_table(self, summary_lines):
        table_html_template = 'academy_tests.impugnments_summary_table'
        table_html = self.env['ir.qweb'].render(
            table_html_template, {'ctx': {'lines': summary_lines}}
        )

        return table_html.decode('utf-8')

    @staticmethod
    def _safe_int(value, default=None):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

