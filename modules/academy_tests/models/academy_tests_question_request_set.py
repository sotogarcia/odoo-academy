# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


from datetime import date, timedelta

_logger = getLogger(__name__)

REQUEST_STATES = [
    ('received', 'Received'),
    ('urgent', 'Urgent'),
    ('completed', 'Completed'),
    ('expired', 'Expired'),
]


class AcademyTestsQuestionRequestSet(models.Model):
    """ Allow to request a set of questions to an especific user
    """

    _name = 'academy.tests.question.request.set'
    _description = u'Academy tests question request'

    _rec_name = 'name'
    _order = 'name ASC'

    _inherit = [
        'ownership.mixin',
        'mail.thread'
    ]

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Name of the request',
        size=1024,
        translate=True,
        track_visibility='onchange'
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='Something about this request',
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help=('If the active field is set to false, it will allow you to '
              'hide record without removing it'),
        track_visibility='onchange'
    )

    expiration = fields.Date(
        string='Expiration',
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self.default_expiration(),
        track_visibility='onchange',
        help='Date before which questions must be provided to cover the demand'
    )

    notified = fields.Date(
        string='Notified',
        required=False,
        readonly=False,
        index=True,
        default=None,
        help='Date of last notification'
    )

    request_ids = fields.One2many(
        string='Requests',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.question.request',
        inverse_name='request_set_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    test_id = fields.Many2one(
        string='Test',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='academy.tests.test',
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

    def default_expiration(self):
        return self._get_date(days=8)

    _sql_constraints = [
        (
            'not_expired',
            'CHECK(expiration > CURRENT_TIMESTAMP(0)::TIMESTAMP)',
            _(u'The expiration date must be after the current instant')
        ),
        (
            'unique_by_tests',
            'UNIQUE(test_id)',
            _('There is already a request for the same test')
        )
    ]

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

    @api.model
    def create(self, values):
        """ Computes state value
        """

        _super = super(AcademyTestsQuestionRequestSet, self)
        result = _super.create(values)

        result.update_state()

        return result

    def write(self, values):
        """ Computes state value
        """

        _super = super(AcademyTestsQuestionRequestSet, self)
        result = _super.write(values)

        if 'state' not in values.keys():
            self.update_state()

        return result

    def _get_request_states(self):
        states = self.mapped('request_ids.state')
        return list(dict.fromkeys(states))

    @staticmethod
    def _min_state(states):
        if states:
            for index in range(0, len(REQUEST_STATES)):
                if REQUEST_STATES[index][0] in states:
                    return REQUEST_STATES[index][0]

        return REQUEST_STATES[0][0]

    def update_state(self, update_requests_before=True):
        if update_requests_before:
            self.request_ids.update_state()

        for record in self:
            states = record._get_request_states()
            record.state = record._min_state(states)

    def remind(self):
        for record in self:
            if record.state != 'completed':
                record.request_ids.remember_request()

    @api.model
    def cron_actions(self):

        domain = []
        active_set = self.env[self._name]
        active_set = active_set.search(domain)

        active_set.update_state(update_requests_before=True)

        if self._cron_is_last_call():

            today = date.today().strftime('%Y-%m-%d')
            yesterday = self._get_date(days=-1).strftime('%Y-%m-%d')
            week_ago = self._get_date(days=-7).strftime('%Y-%m-%d')

            domain = [
                '|',
                '|',
                ('notified', '=', False),
                ('notified', '<=', week_ago),
                '&',
                ('expiration', '>=', yesterday),
                ('notified', '<', today),
            ]
            notify_set = self.env[self._name]
            notify_set = notify_set.search(domain)

            notify_set.remember_request()

    @staticmethod
    def _get_date(days):
        return date.today() + timedelta(days=days)

    def _cron_is_last_call(self):
        """Check if the next time the cron action is called will be tomorrow

        Returns:
            bool: True if next call will be tomorrow or False otherwise
        """

        name = 'ir_cron_academy_tests_question_request_set_cron_actions'

        xid = '{module}.{name}'.format(module='academy_tests', name=name)
        cron_act = self.env.ref(xid)

        tomorrow = self._get_date(days=1)

        return cron_act.nextcall.date() == tomorrow

    @staticmethod
    def _request_values(request):
        return {
            'res_user_id': request.res_user_id.id,
            'order': request.order,
            'minimum': request.minimum,
            'maximum': request.maximum,
            'topic_id': request.topic_id.id,
            'state': 'received',
        }

    def _build_request_operations(self):
        result = [(5, 0, 0)]

        for request in self.request_ids:
            values = self._request_values(request)
            operation = (0, 0, values)
            result.append(operation)

        return result

    def copy(self, default=None):

        if not default:
            default = {}

        if 'name' not in default:
            default['name'] = _("%s (copy)") % self.name

        if 'test_id' not in default:
            test_name = _("%s (copy)") % self.test_id.name
            create_empty_ctx = {'create_empty_test': True}

            test_set = self.test_id.with_context(create_empty_ctx)
            new_test = test_set.copy({'name': test_name})

            default['test_id'] = new_test.id

        if self.request_ids:
            default['request_ids'] = self._build_request_operations()

        _super = super(AcademyTestsQuestionRequestSet, self)
        result = _super.copy(default)

        return result
