# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo.http import route, request
from .base_controller import BasePublicController
from odoo.tools.translate import _

from logging import getLogger


ROUTE = "/civil-service-tracker/web/public-offer/item/<string:token>"


_logger = getLogger(__name__)


class WebPublicOfferItem(BasePublicController):
    @route(
        ROUTE,
        type="http",
        auth="user",
        website=True,
        csrf=True,
        methods=["GET"],
    )
    def web_public_offer_item(self, token=None, **kwargs):
        pass
