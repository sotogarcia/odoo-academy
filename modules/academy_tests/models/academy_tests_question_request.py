# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger
from odoo.exceptions import ValidationError, UserError
from .utils.libuseful import fix_established, is_numeric
from .utils.sql_inverse_searches import REQUEST_SUPPLIED_COUNT_SEARCH

from datetime import timedelta, date

_logger = getLogger(__name__)


REQUEST_STATES = [
    ('received', 'Received'),
    ('urgent', 'Urgent'),
    ('completed', 'Completed'),
    ('expired', 'Expired'),
]


class AcademyTestsQuestionRequest(models.Model):
    """ Allow to request a set of questions to an especific user
    """

    _name = 'academy.tests.question.request'
    _description = u'Academy tests question request'

    _rec_name = 'id'
    _order = 'id DESC'

    _inherit = ['mail.thread']

    # _inherits = {'academy.tests.question.request.set': 'request_set_id'}

    request_set_id = fields.Many2one(
        string='Request set',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Choose parent request set',
        comodel_name='academy.tests.question.request.set',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        track_visibility='onchange'
    )

    res_user_id = fields.Many2one(
        string='User',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Select the user who is the subject of the demand',
        comodel_name='res.users',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        track_visibility='onchange'
    )

    order = fields.Text(
        string='Order',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this request',
        translate=True
    )

    minimum = fields.Integer(
        string='Minimum',
        required=True,
        readonly=False,
        index=False,
        default=10,
        help='Minimum number of questions that must be provided',
        track_visibility='onchange'
    )

    maximum = fields.Integer(
        string='Maximum',
        required=True,
        readonly=False,
        index=False,
        default=10,
        help='Maximum number of questions that can be provided',
        track_visibility='onchange'
    )

    question_ids = fields.One2many(
        string='Questions',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help=False,
        comodel_name='academy.tests.test.question.rel',
        inverse_name='request_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    supplied = fields.Integer(
        string='Supplied',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Show number of supplied questions',
        store=False,
        compute='_compute_supplied',
        search='_search_supplied'
    )

    topic_id = fields.Many2one(
        string='Topic',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help=False,
        comodel_name='academy.tests.topic',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    state = fields.Selection(
        string='State',
        required=False,
        readonly=False,
        index=False,
        default=REQUEST_STATES[0][0],
        help='Current wizard step',
        selection=REQUEST_STATES,
        group_expand='_expand_states'
    )

    name = fields.Char(
        string='Name',
        related='request_set_id.name'
    )

    description = fields.Text(
        string='Description',
        related='request_set_id.description'
    )

    expiration = fields.Date(
        string='Expiration',
        related='request_set_id.expiration'
    )

    owner_id = fields.Many2one(
        string='Owner',
        related='request_set_id.owner_id'
    )

    test_id = fields.Many2one(
        string='Test',
        related='request_set_id.test_id'
    )

    @api.depends('question_ids')
    def _compute_supplied(self):
        for record in self:
            record.supplied = len(record.question_ids)

    def _search_supplied(self, operator, value):
        supported = ['=', '!=', '<=', '<', '>', '>=']

        assert operator in supported, \
            UserError(_('Search operator not supported'))

        assert is_numeric(value) or value in [True, False], \
            UserError(_('Search value not supported'))

        operator, value = fix_established(operator, value)

        sql = REQUEST_SUPPLIED_COUNT_SEARCH.format(operator, value)

        self.env.cr.execute(sql)
        ids = self.env.cr.fetchall()

        return [('id', 'in', ids)]

    @api.onchange('minimum')
    def _onchange_minimum(self):
        if self.maximum < self.minimum:
            self.maximum = self.minimum

    _sql_constraints = [
        (
            'positive_values',
            'CHECK(minimum > 0 AND maximum > 0)',
            _(u'The number of questions must be a positive integer')
        ),
        (
            'maximum_goe_minimum',
            'CHECK(minimum <= maximum)',
            _(u'Maximum must be greater than or equal to minimum value')
        ),
        # (
        #     'ensure_unique_request',
        #     'UNIQUE(request_set_id, res_user_id, order, topic_id)',
        #     _(u'The request cannot be repeated in the set')
        # ),
    ]

    def name_get(self):
        result = []
        for record in self:
            if not record.order:
                name = record.request_set_id.name
            else:
                name = record.order[:22] + '...'

            result.append((record.id, name))

        return result

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

    @api.model
    def create(self, values):
        """ Computes state value
        """

        _super = super(AcademyTestsQuestionRequest, self)
        result = _super.create(values)

        result.update_state()

        return result

    def write(self, values):
        """ Computes state value
        """

        _super = super(AcademyTestsQuestionRequest, self)
        result = _super.write(values)

        if 'state' not in values.keys():
            self.update_state()

        return result

    def update_state(self):
        now = fields.Date.today()

        for record in self:
            expiration = record.request_set_id.expiration or date.min

            if len(record.question_ids) >= record.minimum:
                record.state = 'completed'
            elif expiration < now:
                record.state = 'expired'
            elif now >= (expiration - timedelta(days=1)):
                record.state = 'urgent'
            else:
                record.state = 'received'

        request_set_ids = self.mapped('request_set_id')
        request_set_ids.update_state(update_requests_before=False)

    def remember_request(self):
        xid = 'academy_tests.mail_template_required_questions_reminder'
        mail_template = self.env.ref(xid)

        for record in self:
            mail_template.send_mail(record.id)

    def remember_verification(self):
        xid = 'academy_tests.mail_template_verify_questions_reminder'
        mail_template = self.env.ref(xid)

        for record in self:
            mail_template.send_mail(record.id)

    def notify(self):
        to_verify_set = self.filtered(lambda x: x.supplied >= x.minimum)
        to_verify_set.remember_verification()

        to_request_set = self.filtered(lambda x: x.supplied < x.minimum)
        to_request_set.remember_request()

    def autocomplete_wizard(self):
        self.ensure_one()

        test_kind_xid = 'academy_tests.academy_tests_test_kind_common'
        test_kind_item = self.env.ref(test_kind_xid)

        quantity = max(0, self.minimum - self.supplied)

        values = {
            'name': self.request_set_id.name,
            'description': self.order,
            'active': True,
            'owner_id': self.request_set_id.owner_id.id,
            'test_kind_id': test_kind_item.id,
            'random_line_ids': [(0, 0, {
                'name': self.order or _('Line 1'),
                'description': _('{} questions'.format(quantity)),
                'active': True,
                'sequence': 1,
                'quantity': quantity,
                'test_ids': [(4, self.request_set_id.test_id.id, None)],
                'exclude_tests': True,
                'owner_ids': [(4, self.res_user_id.id, None)],
                'authorship': 'own',
            })]
        }

        if self.topic_id:
            topic_values = {
                'topic_id': self.topic_id.id
            }

            domain = [('topic_id', '=', self.topic_id.id)]
            version_set = self.env['academy.tests.topic.version']
            version_set = version_set.search(
                domain, order='sequence DESC', limit=1)
            if version_set:
                topic_values['topic_version_ids'] = [(4, version_set.id, 0)]

            values['random_line_ids'][0][2]['categorization_ids'] = \
                [(0, 0, topic_values)]

        template_set = self.env['academy.tests.random.template']
        template_set = template_set.create(values)

        return {
            'type': 'ir.actions.act_window',
            'model': 'ir.actions.act_window',
            'name': _('Populate'),
            'res_model': 'academy.tests.random.wizard',
            'view_mode': 'form',
            'target': 'new',
            'domain': [],
            'context': {
                'default_random_template_id': template_set.id,
                'append_only': True,
                'request_id': self.id,
                'with_user_id': self.owner_id.id,
                'default_shuffle': False
            },
        }

    def import_wizard(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'model': 'ir.actions.act_window',
            'name': _('Import'),
            'res_model': 'academy.tests.question.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'domain': [],
            'context': {
                'default_test_id': self.request_set_id.test_id.id,
                'request_id': self.id,
                'with_user_id': self.owner_id.id
            },
        }

    def generate_url(self):
        """Build the URL to the record's form view.
          - Base URL + Database Name + Record ID + Model Name

        Returns:
            str: string with url
        """

        self.ensure_one()

        pattern = '{}web?db={}#id={}&view_type=form&model={}'

        param = self.env['ir.config_parameter']
        base_url = param.get_param('web.base.url')

        if base_url and base_url[-1:] != '/':
            base_url += '/'

        db = self._cr.dbname

        return pattern.format(base_url, db, self.id, self._name)
