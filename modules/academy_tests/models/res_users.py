# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from logging import getLogger

_logger = getLogger(__name__)

UTPL = 'academy_tests.mail_template_uncategorized_questions_by_user_and_topic'
DTPL = 'academy_tests.mail_template_duplicated_questions_by_user_and_topic'
ITPL = 'academy_tests.mail_template_you_have_impugnments'


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

        owner_ids = impugnment_set.mapped('owner_id.id')
        owner_ids = list(dict.fromkeys(owner_ids))

        user_domain = [('id', 'in', owner_ids)]
        user_set = self.env['res.users']
        user_set = user_set.search(user_domain)

        mail_template = self.env.ref(ITPL)
        for user_item in user_set.sorted('name'):
            _logger.info(msg, user_item.name)
            mail_template.send_mail(user_item.id)
