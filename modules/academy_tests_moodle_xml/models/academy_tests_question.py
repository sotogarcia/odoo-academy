# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger

import lxml.etree as ET
import mimetypes
from io import BytesIO

_logger = getLogger(__name__)


class AcademyTestsQuestion(models.Model):
    """ Allow to export questions as Moodle XML
    """

    _inherit = ['academy.tests.question']

    @staticmethod
    def _moodle_cdata(text=None):
        return ET.CDATA(text) if text else ''

    @staticmethod
    def _moodle_paragraphs(text, prettify=True):
        paragraphs = []
        lines = text.splitlines()
        sep = '\n' if prettify else ''

        for line in lines:
            paragraphs.append('<p>{}</p>'.format(line))

        return sep.join(paragraphs)

    @staticmethod
    def _moodle_create_node(multichoice=False):
        node = ET.Element('question', type='multichoice')

        ET.SubElement(node, 'hidden').text = '0'
        ET.SubElement(node, 'shuffleanswers').text = 'false'
        ET.SubElement(node, 'answernumbering').text = 'abc'
        ET.SubElement(node, 'single').text = 'false' if multichoice else 'true'

        return node

    def _moodle_append_name(self, node, name=None):
        if not name:
            name = '{}-{}'.format('ID', self.id)

        sub = ET.SubElement(node, 'name')
        ET.SubElement(sub, 'text').text = name

    def _moodle_append_description(self, node, prettify=True):
        description = self._moodle_paragraphs(self.description or '', prettify)
        sub = ET.SubElement(
            node, 'generalfeedback', format='moodle_auto_format')
        ET.SubElement(sub, 'text').text = self._moodle_cdata(description)

    def _moodle_append_statement(self, node, prettify=True):
        tag = '<img src="@@PLUGINFILE@@/{fn}" alt="{fn}" role="presentation">'
        html = ''

        snode = ET.SubElement(node, 'questiontext', format='html')

        if self.ir_attachment_ids:
            pattern = '<div style="display: flex;">{}</div>{}'
            sep = '\n' if prettify else ''
            img_tags = []

            for attach in self.ir_attachment_ids:
                ext = mimetypes.guess_extension(attach.mimetype)
                fname = '{}{}'.format(attach.name, ext)

                attnode = ET.SubElement(
                    snode, 'file', name=fname, path="/", encoding="base64")
                attnode.text = attach.datas

                img_tags.append(tag.format(fn=fname))

            html += pattern.format(sep.join(img_tags), sep)

        if self.preamble:
            html += self._moodle_paragraphs(self.preamble or '', prettify)

        html += self._moodle_paragraphs(self.name or '', prettify)

        ET.SubElement(snode, 'text').text = self._moodle_cdata(html)

    def _moodle_append_answer(self, node, answer, fraction):
        ans_node = ET.SubElement(
            node, 'answer', format='moodle_auto_format', fraction=fraction)
        ET.SubElement(ans_node, 'text').text = self._moodle_cdata(answer.name)

        desc_node = ET.SubElement(
            ans_node, 'feedback', format='moodle_auto_format')
        ET.SubElement(desc_node, 'text').text = \
            self._moodle_cdata(answer.description or '')

    def _to_moodle(self, name=None):
        self.ensure_one()

        a_total, a_right = self._answer_count()
        good = 100 / a_right
        bad = (100 / (a_total - a_right)) * -1

        node = self._moodle_create_node(multichoice=(a_right > 1))

        self._moodle_append_name(node, name)
        self._moodle_append_statement(node)
        self._moodle_append_description(node)

        for answer in self.answer_ids:
            fraction = str(good) if answer.is_correct else str(bad)

            self._moodle_append_answer(node, answer, fraction)

        return node

    def download_as_moodle_xml(self):
        question_ids = self.mapped('id')

        if not question_ids:
            raise(_('There are no questions'))

        ids_str = ','.join([str(item) for item in question_ids])

        relative_url = '/academy_tests/moodle/questions?question_ids={}'
        return {
            'type': 'ir.actions.act_url',
            'url': relative_url.format(ids_str),
            'target': 'self',
        }

    def to_moodle(self, encoding='utf8', prettify=True, xml_declaration=True,
                  category=None):
        quiz = self._moodle_create_quiz(category=category)

        for record in self:
            node = record._to_moodle()
            quiz.append(node)

        file = BytesIO()
        root = quiz.getroottree()
        root.write(file, encoding=encoding, pretty_print=prettify,
                   xml_declaration=xml_declaration)

        return file.getvalue()

    @staticmethod
    def _moodle_create_quiz(category=None):
        category = category or _('Odoo export')

        node = ET.Element('quiz')

        qnode = ET.SubElement(node, 'question', type='category')
        cnode = ET.SubElement(qnode, 'category')
        ET.SubElement(cnode, 'text').text = '$course$/top'

        qnode = ET.SubElement(node, 'question', type='category')
        cnode = ET.SubElement(qnode, 'category')
        ET.SubElement(cnode, 'text').text = '$course$/top/{}'.format(category)

        return node

    def _answer_count(self):
        self.ensure_one()

        right_set = self.answer_ids.filtered(lambda a: a.is_correct)

        return len(self.answer_ids), len(right_set)
