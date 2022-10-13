# -*- coding: utf-8 -*-
######################################################################################################
#
# Copyright (C) B.H.C. sprl - All Rights Reserved, http://www.bhc.be
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied,
# including but not limited to the implied warranties
# of merchantability and/or fitness for a particular purpose
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
######################################################################################################
import logging
try:
    from BytesIO import BytesIO
except ImportError:
    from io import BytesIO
import zipfile
from datetime import datetime
from odoo import http
from odoo.http import request, Response
from odoo.http import content_disposition
import mimetypes
import os
from odoo.tools.translate import _
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)


class TestAttachments(http.Controller):

    @staticmethod
    def _safe_cast(val, to_type, default=None):
        try:
            return to_type(val)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _has_extension(fname):
        fname, ext = os.path.splitext(fname)

        return bool(ext)

    @staticmethod
    def _get_extension(attachment):
        return mimetypes.guess_extension(attachment.mimetype)

    def _attachment_file_name(self, attachment):
        file_name = '{0:08}'.format(attachment.id)
        attach_name = attachment.name

        if not self._has_extension(attach_name):
            ext = self._get_extension(attachment) or '.dat'
            attach_name = '{}{}'.format(file_name, ext)

        return attach_name

    @http.route('/academy_tests/attachments', type='http', auth="public")
    def download_document(self, test_id, zname=None, **kw):
        test_id = self._safe_cast(test_id, int, 0)

        test_set = request.env['academy.tests.test']
        test_set = test_set.browse(test_id)

        mapped_path = 'question_ids.question_id.ir_attachment_ids.id'
        attachment_ids = test_set.mapped(mapped_path)

        attachment_domain = [('id', 'in', attachment_ids)]
        attachment_set = request.env['ir.attachment']
        attachment_set = attachment_set.search(attachment_domain)

        file_dict = {}
        for attachment_id in attachment_set:
            file_store = attachment_id.store_fname
            if file_store:
                file_name = self._attachment_file_name(attachment_id)
                file_path = attachment_id._full_path(file_store)
                file_dict["%s:%s" % (file_store, file_name)] = \
                    dict(path=file_path, name=file_name)

        if not zname:
            zname = '{0:08}.zip'.format(test_id)

        bitIO = BytesIO()
        zip_file = zipfile.ZipFile(bitIO, "w", zipfile.ZIP_DEFLATED)
        for file_info in file_dict.values():
            zip_file.write(file_info["path"], file_info["name"])
        zip_file.close()

        headers = [('Content-Type', 'application/x-zip-compressed'),
                   ('Content-Disposition', content_disposition(zname))]

        return request.make_response(bitIO.getvalue(), headers=headers)

    @http.route('/academy_tests/source', type='http', auth="public")
    def download_source(self, question_ids, zname=None, **kw):
        question_ids = [int(item) for item in question_ids.split(',') if item]

        domain = [('id', 'in', question_ids)]
        question_set = request.env['academy.tests.question']
        question_set = question_set.search(domain)

        content = question_set.to_string(True)
        content = content.encode('utf_8', errors='replace')

        attachment_ids = question_set.mapped('ir_attachment_ids.id')

        attachment_domain = [('id', 'in', attachment_ids)]
        attachment_set = request.env['ir.attachment']
        attachment_set = attachment_set.search(attachment_domain)

        file_dict = {}
        for attachment_id in attachment_set:
            file_store = attachment_id.store_fname
            if file_store:
                file_name = self._attachment_file_name(attachment_id)
                file_path = attachment_id._full_path(file_store)
                file_dict["%s:%s" % (file_store, file_name)] = \
                    dict(path=file_path, name=file_name)

        zname = zname or '{}.zip'.format(_('Questions'))
        tname = '{}.txt'.format(_('Statement'))
        dname = _('Resources')

        bitIO = BytesIO()
        zip_file = zipfile.ZipFile(bitIO, "w", zipfile.ZIP_DEFLATED)
        zip_file.writestr(tname, content)
        for file_info in file_dict.values():
            target_path = os.path.join(dname, file_info["name"])
            zip_file.write(file_info["path"], target_path)
        zip_file.close()

        headers = [('Content-Type', 'application/x-zip-compressed'),
                   ('Content-Disposition', content_disposition(zname))]

        return request.make_response(bitIO.getvalue(), headers=headers)

    @http.route('/academy_tests/moodle/test', type='http', auth="public")
    def test_to_moodle(self, test_id, category=None, **kw):

        try:
            test_set = self._browse_for_test(test_id)
            question_set = test_set.question_ids
        except AssertionError as ae:
            return Response(str(ae), status=404)

        headers = self._build_moodle_headers(test_set.name)
        content = self._build_moodle_xml(
            question_set, category or test_set.name)

        return request.make_response(content, headers=headers)

    @http.route('/academy_tests/moodle/questions', type='http', auth="public")
    def questions_to_moodle(self, question_ids, category=None, **kw):

        try:
            question_set = self._search_for_questions(question_ids)
        except AssertionError as ae:
            return Response(str(ae), status=404)

        content = self._build_moodle_xml(question_set, category)
        headers = self._build_moodle_headers()

        return request.make_response(content, headers=headers)

    def _browse_for_test(self, test_id_str, verify=True):
        test_set = request.env['academy.tests.test']

        test_id = self._safe_cast(test_id_str, int, 0)

        if test_id:
            test_set = test_set.browse(test_id)

        if verify:
            assert test_set, _('The requested test was not found')

        return test_set

    @http.route('/academy_tests/test/preview', type='http', auth="public")
    def test_preview(self, test_id, **kw):

        try:
            test_set = self._browse_for_test(test_id)
            xid = 'academy_tests.action_report_preview_test'
            report = request.env.ref(xid)
            html = report.render_qweb_html(test_set.id)[0]
        except AssertionError as ae:
            return Response(str(ae), status=404)
        except Exception as ex:
            _logger.error(ex)
            return Response('Unable to display preview. See logs.', status=404)

        httpheaders = [
            ('Content-Type', 'text/html; charset=utf-8'),
            ('Content-Length', len(html))
        ]

        return request.make_response(html, headers=httpheaders)

    def _search_for_questions(self, question_str, verify=True):
        question_set = request.env['academy.tests.question']

        question_str = question_str or ''
        question_ids = [int(item) for item in question_str.split(',') if item]
        if question_ids:
            domain = [('id', 'in', question_ids)]
            question_set = question_set.search(domain)

        if verify:
            assert question_set and (len(question_set) == len(question_ids)), \
                _('Some of the requested questions were not found')

        return question_set

    @staticmethod
    def _build_moodle_xml(question_set, category=None):
        category = category or _('Odoo export')

        return question_set.to_moodle(encoding='utf8', prettify=True,
                                      xml_declaration=True,
                                      category=category)

    @staticmethod
    def _build_moodle_headers(fname=None):
        if not fname:
            pattern = datetime.now().strftime('{} %Y-%m-%d %H-%M-%S')
            fname = pattern.format(_('Odoo export'))

        fname = '{}.xml'.format(fname)

        return [('Content-Type', 'text/xml'),
                ('Content-Disposition', content_disposition(fname))]
