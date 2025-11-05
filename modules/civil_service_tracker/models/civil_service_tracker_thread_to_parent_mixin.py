# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _

from logging import getLogger


_logger = getLogger(__name__)


class CivilServiceTrackerThreadToParentMixin(models.AbstractModel):
    _name = "civil.service.tracker.thread.to.parent.mixin"
    _description = "Civil service tracker thread to parent"

    _inherit = "mail.thread"

    # -------------------------------------------------------------------------
    # OVERWRITTEN METHODS
    # -------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, values_list):
        parent = super(CivilServiceTrackerThreadToParentMixin, self)
        records = parent.create(values_list)

        records._message_change_thread_to_parent_process()

        return records

    def write(self, vals):
        parent = super(CivilServiceTrackerThreadToParentMixin, self)
        result = parent.write(vals)

        self._message_change_thread_to_parent_process()

        return result

    def _message_change_thread_to_parent_process(self):
        for record in self:
            parent_id = record._get_tracking_parent()

            if parent_id:
                record.message_change_thread(parent_id)

    def _message_track(self, tracked_fields, initial):
        parent = super(CivilServiceTrackerThreadToParentMixin, self)
        tracked = parent._message_track(tracked_fields, initial)

        prefix = self._get_tracking_prefix()
        if self._is_tracked_as_expected(tracked):
            for item in tracked[1]:
                if self._is_tracked_item_as_expected(item):
                    item[2][
                        "field_desc"
                    ] = f'{prefix} >> {item[2]["field_desc"]}'

        return tracked

    def _get_tracking_prefix(self):
        return _("Child record")

    def _get_tracking_parent(self):
        msg = "You need to implement %s method before use %s"
        raise NotImplementedError(msg % ("", self._name))

    # -------------------------------------------------------------------------
    # AUXILIARY METHODS
    # -------------------------------------------------------------------------

    @staticmethod
    def _is_tracked_as_expected(tracked):
        return (
            isinstance(tracked, (tuple, list))
            and len(tracked) == 2
            and isinstance(tracked[1], list)
        )

    @staticmethod
    def _is_tracked_item_as_expected(item):
        return (
            isinstance(item, list)
            and len(item) == 3
            and isinstance(item[2], dict)
            and "field_desc" in item[2]
        )
