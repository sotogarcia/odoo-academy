# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo.http import route, request, Controller
from odoo.tools.translate import _
from odoo.osv.expression import FALSE_DOMAIN

from logging import getLogger
from uuid import UUID
from urllib.parse import urlparse, urljoin


_logger = getLogger(__name__)


class BasePublicController(Controller):
    @classmethod
    def _make_token_domain(cls, token):
        if token and cls._is_valid_token(token):
            domain = [("token", "=", token)]
            _logger.debug(f"Process info requested with token: {token}")
        else:
            _logger.warning(f"Invalid process token: {token}")
            domain = FALSE_DOMAIN

        return domain

    @staticmethod
    def _is_valid_token(token):
        try:
            val = UUID(token, version=4)
            return str(val) == token.lower()
        except ValueError:
            return False

    @staticmethod
    def _get_current_user():
        return http.request.env.user

    @staticmethod
    def remove_scheme(url):
        parsed = urlparse(url)
        netloc_and_path = parsed.netloc + parsed.path
        return netloc_and_path

    @staticmethod
    def secure_absolute_url(relative_url):
        """
        Safely builds an absolute URL from a relative path using the current host URL.

        If an exception occurs, returns '#'.
        """
        url = "#"

        try:
            base_url = request.httprequest.host_url
            url = urljoin(base_url, relative_path)
        except Exception as ex:
            _logger.exception(ex)

        return url
