# -*- coding: utf-8 -*-
""" AcademyAbstractSpreadable
"""

from logging import getLogger
from odoo import models, fields, api

# pylint: disable=locally-disabled, C0103
_logger = getLogger(__name__)


class AcademyAbstractSpreadable(models.AbstractModel):
    """ Propagate message with certain subtype to all models listed in
    spread_to attribute

    _spread_to = {'subtype.external.id': [related_field, ...]}
    """

    _name = 'academy.abstract.spreadable'
    _description = u'Overrides message_post to propagate message'

    def _spread_to(self, subtype_id=False, subtype=None):
        return []

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, *, subtype_id=False, subtype=None, **kwargs):

        target_list = self._spread_to(subtype_id, subtype)
        for target_set in target_list:
            for target_item in target_set:

                target_item.message_post(
                    subtype_id=subtype_id, subtype=subtype, **kwargs)

        return super(AcademyAbstractSpreadable, self).message_post(
            subtype_id=subtype_id, subtype=subtype, **kwargs)

# self, *,
# body='', subject=None, message_type='notification',
# email_from=None, author_id=None, parent_id=False,
# subtype_id=False, subtype=None, partner_ids=None,
# channel_ids=None, attachments=None,
# attachment_ids=None, add_sign=True,
# record_name=False, **kwargs
