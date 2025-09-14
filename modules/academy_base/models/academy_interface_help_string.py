# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger

from odoo.exceptions import UserError

_logger = getLogger(__name__)


class AcademyInterfaceHelpString(models.Model):
    """Allow to save the strings that will be displayed to the user on the
    interface as help.
    """

    _name = "academy.interface.help.string"
    _description = "Academy interface help string"

    _rec_name = "name"
    _order = "name ASC"

    name = fields.Char(
        string="Name",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Key will be used to recover help string",
        size=36,
        translate=False,
    )

    description = fields.Text(
        string="Description",
        required=True,
        readonly=False,
        index=True,
        default=None,
        help="Texto of the text string",
        translate=True,
    )

    _sql_constraints = [
        (
            "unique_name",
            'UNIQUE("name")',
            "There already exists an interface help string with that name",
        )
    ]

    @api.model
    def get_by_name(self, name):
        help_domain = [("name", "=", name)]
        help_obj = self.env[self._name]
        help_item = help_obj.search(help_domain, limit=1)

        return help_item.description or _("No help text found")

    @api.model
    def get_by_ref(self, xmlid):
        if isinstance(xmlid, (tuple, list)) and len(xmlid) == 2:
            xmlid = ".".join(xmlid)
        elif not isinstance(str):
            msg = _("Invalid external identifier «{}» for help string")
            raise UserError(msg.format(xmlid))

        imd_obj = self.env["ir.model.data"]
        help_item = imd_obj.xmlid_to_object(xmlid, raise_if_not_found=False)

        if help_item and help_item.description:
            description = help_item.description
        else:
            description = _("No help text found")

        return description
