# -*- coding: utf-8 -*-
""" AcademyAbstractOwner
"""

from logging import getLogger
from odoo import models, fields, api

# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)


# pylint: disable=locally-disabled, R0903,W0212
class AcademyAbstractOwner(models.AbstractModel):
    """ Models can extend this to touch related models through 'x2many' fields
    """

    _name = 'academy.abstract.owner'
    _description = u'Provides owner field and behavior'

    _min_group_allowed = 'academy_base.academy_group_technical'

    owner_id = fields.Many2one(
        string='Owner',
        required=True,
        readonly=False,
        index=True,
        default=lambda self: self._default_owner_id(),
        help='Current owner',
        comodel_name='res.users',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        track_visibility='onchange'
    )

    def _default_owner_id(self):
        """ Compute the default owner for new questions; this will be
        the current user or the root user.
        @note: root user will be used only for background actions.
        """

        return self.env.context.get('uid', 1)

    def _get_user(self, owner_id):
        """ Get res.users model related with given owner_id

        Arguments:
            owner_id {int} -- ID of the owner to which user will be browse

        Returns:
            recordset -- single item recorset with the user
        """

        return self.env['res.users'].browse(owner_id)

    def _is_follower(self, user_item):
        """ Check if given user is follows current self (single) record

        Arguments:
            user_item {recordset} -- res.users single item recordset

        Returns:
            bool -- True if given user follows self (single) record
        """

        followers_obj = self.env['mail.followers']

        domain = [
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('partner_id', '=', user_item.partner_id.id)
        ]

        return len(followers_obj.search(domain)) > 0

    def _pick_owner(self, values):
        """ Appends current user as owner_id in given values dictionary

        This method will be used in ``create`` method

        Arguments:
            values {dict} -- dictionary with pairs field: value
        """

        owner_id = values.get('owner_id', False)
        uid = self.env.context.get('uid')
        if owner_id and owner_id != uid:
            user_item = self.env['res.users'].browse(uid)
            if not user_item.has_group(self._min_group_allowed):
                values['owner_id'] = uid

    def _pop_owner(self, values):
        """ Removes ``owner_id`` key and value from given values dictionary

        This method will be used in ``write`` method

        Arguments:
            values {dict} -- dictionary with pairs field: value
        """

        owner_id = values.get('owner_id', False)
        if owner_id:
            uid = self.env.context.get('uid')
            user_item = self.env['res.users'].browse(uid)
            if not user_item.has_group(self._min_group_allowed):
                values.pop('owner_id')

    def _create_new_mail_followers(self, user_item):
        """ Create a mail.followers record link given user as follower of the
        current record.

        Arguments:
            user_item {recordset} -- res.users single recordset

        Returns:
            recordset -- mail.followers single recordset
        """

        followers_obj = self.env['mail.followers']

        new_item = followers_obj.create({
            'res_model': self._name,
            'res_id': self.id,
            'partner_id': user_item.partner_id.id,
            'channel_id': None
        })

        return new_item

    def _ensure_owner_as_follower(self, values):
        """ For each one of records in self, this checks if owner is a
        follower, otherwise this makes it a follower

        Arguments:
            values {dict} -- dictionary with pairs field: value
        """
        for record in self:
            owner_id = values.get('owner_id', False)

            if owner_id:

                user_item = record._get_user(owner_id)
                if user_item and not record._is_follower(user_item):
                    record._create_new_mail_followers(user_item)

    @api.model
    def create(self, values):
        """ Prevent unauthorized users from changing ownership for others other
        than themselves.

        Appends owner to mail.followers list.
        """

        self._pick_owner(values)

        result = super(AcademyAbstractOwner, self).create(values)

        result._ensure_owner_as_follower(values)

        return result

    def write(self, values):
        """ Prevent unauthorized users from changing ownership for others other
        than themselves.

        Appends owner to mail.followers list.
        """

        self._pop_owner(values)

        result = super(AcademyAbstractOwner, self).write(values)

        self._ensure_owner_as_follower(values)

        return result
