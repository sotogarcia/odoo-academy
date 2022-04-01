# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from logging import getLogger

import re


_logger = getLogger(__name__)


class AcademyTestsAnswer(models.Model):
    """ Extend academy.tests.answer functionality adding a new computed fild
    witch will contain a valid GIFT code to export the question
    https://docs.moodle.org/38/en/GIFT_format#Format_symbols_explained

    Fields:
        gift (Text): GIFT code to export to Moodle
    """

    _inherit = 'academy.tests.answer'

    gift = fields.Text(
        string='Gift',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Exportable GIFT format',
        translate=False,
        compute=lambda self: self._compute_gift()
    )

    @api.depends('name', 'description')
    def _compute_gift(self):
        """ Fills the gift field with exported data from the answer in GIFT
        format
        // https://docs.moodle.org/38/en/GIFT_format#Format_symbols_explained
        """

        for record in self:
            prefix = '= ' if record.is_correct else '~ '

            record.gift = prefix + record._gift_scape_string(record.name)

            if record.description:
                desc = record._gift_scape_string(record.description)
                record.gift += '\n#' + desc

    @staticmethod
    def _gift_scape_string(in_str):
        """ Following characters ~=#{}: are not valid to be usded in GIFT text
        This method scapes them and the new line character too
        """

        in_str = in_str or ''

        if in_str:
            pattern = re.compile('([~=#{}:])')
            in_str = pattern.sub(r'\\\1', in_str)

            pattern = re.compile(r'\n')
            in_str = pattern.sub(r'\\n', in_str)

        return in_str
