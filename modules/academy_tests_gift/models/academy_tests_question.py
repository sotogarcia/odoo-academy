# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger


import re

_logger = getLogger(__name__)


class AcademyTestsQuestion(models.Model):
    """ Extend academy.tests.question functionality adding a new computed fild
    witch will contain a valid GIFT code to export the question
    https://docs.moodle.org/38/en/GIFT_format#Format_symbols_explained

    Fields:
        gift (Text): GIFT code to export to Moodle
    """

    _inherit = ['academy.tests.question']

    gift = fields.Text(
        string='Gift',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Exportable GIFT format',
        translate=False,
        compute=lambda self: self._compute_gift(),
        store=False
    )

    @api.depends('name', 'preamble', 'description', 'answer_ids',
                 'create_uid', 'create_date', 'write_uid', 'write_date')
    def _compute_gift(self):
        """ Fills the gift field using GIFT format
            https://docs.moodle.org/38/en/GIFT_format#Format_symbols_explained
        """

        for record in self:
            record.gift = record.to_gift()

    def to_gift(self, title=None):
        self.ensure_one()

        gift = '\n{}\n'.format(self._gift_category())
        gift += self._gift_description()
        gift += title or self._gift_title()
        gift += self._gift_text()
        gift += self._gift_answers()

        return gift

    @staticmethod
    def _gift_scape_string(in_str):
        pattern = re.compile('([~=#{}:])')
        in_str = pattern.sub(r'\\\1', (in_str or ''))

        pattern = re.compile(r'\n')
        in_str = pattern.sub(r'\\n', in_str)

        return in_str

    def _get_date(self, in_dt):
        """ Get (only) date, with timezone, from a given datetime field value
        """
        date_str = ''

        try:
            py_date = fields.Datetime.from_string(in_dt)
            from_timezone = fields.Datetime.context_timestamp(self, py_date)
            date_str = fields.Datetime.to_string(from_timezone)[:10]
        except Exception:
            msg = _('Given argument in_dt ({}) is not a valid datetime value')
            _logger.warning(msg)

        return date_str

    def _gift_description(self, new_line=True):
        """ Build a valid gift descrption using record special fields
        // https://docs.moodle.org/38/en/GIFT_format#Format_symbols_explained
        """

        owner_id = self.owner_id.name or self.create_uid.name or _('unknown')
        write_uid = self.write_uid.name or _('unknown')

        create_date = self._get_date(self.create_date) or '1900-00-00'
        write_date = self._get_date(self.write_date) or '1900-00-00'

        return _('// Author: {} ({}) / Last edit: {} ({}){}').format(
            owner_id,
            create_date,
            write_uid,
            write_date,
            '\n' if new_line else ''
        )

    def _gift_title(self, new_line=True):
        """ Build a valid gift title using record ID
        // https://docs.moodle.org/38/en/GIFT_format#Format_symbols_explained
        """
        pattern = '::QID-{}::{}'
        return pattern.format(self.id, '\n' if new_line else '')

    def _gift_feedback(self, new_line=True):
        """ Build a valid gift global feedbak using record description
        // https://docs.moodle.org/38/en/GIFT_format#Format_symbols_explained
        """

        desc = ''

        if self.description:
            desc = self._gift_scape_string(self.description)
            desc = '#### {}{}'.format(desc, '\n' if new_line else '')

        return desc

    def _gift_text(self, new_line=False):
        """ Build a valid gift question text using preamble and name
        // https://docs.moodle.org/38/en/GIFT_format#Format_symbols_explained
        """

        text = self._gift_scape_string(self.name)

        if self.preamble:
            text = self._gift_scape_string(self.preamble) + '\\n ' + text

        return text if not new_line else text + '\n'

    def _gift_answers(self, global_feedback=True, new_line=True):

        ans_text = ''
        for answer in self.answer_ids:
            ans_text += '{}\n'.format(answer.gift)

        if global_feedback and self.description:
            ans_text += '{}'.format(self._gift_feedback())

        # Next line has a required space at the begining.
        return ' {{\n{}}}{}'.format(ans_text, '\n' if new_line else '')

    def _gift_category(self, new_line=True):

        topic = self._gift_scape_string(self.topic_id.name)
        text = '$CATEGORY: $system$/{}'.format(topic)

        for category_id in self.category_ids:
            text += '/{}'.format(self._gift_scape_string(category_id.name))

        return '{}{}'.format(text, '\n' if new_line else '')

    # @api.onchange('description')
    # def _onchange_description(self):
    #     super(AcademyTestsQuestion, self)._onchange_description()
    #     self.gift = self.to_gift()

    # @api.onchange('preamble')
    # def _onchange_preamble(self):
    #     super(AcademyTestsQuestion, self)._onchange_preamble()
    #     self.gift = self.to_gift()

    # @api.onchange('name')
    # def _onchange_name(self):
    #     super(AcademyTestsQuestion, self)._onchange_name()
    #     self.gift = self.to_gift()

    # @api.onchange('answer_ids')
    # def _onchange_answer_ids(self):
    #     super(AcademyTestsQuestion, self)._onchange_answer_ids()
    #     self.gift = self.to_gift()
