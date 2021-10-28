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
from odoo.http import request
from odoo.http import content_disposition
import mimetypes
import os

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
        fname = attachment.name

        if not self._has_extension(fname):
            ext = self._get_extension(attachment) or '.dat'
            fname = '{}{}'.format(fname, ext)

        return fname

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
                print(file_name)
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
