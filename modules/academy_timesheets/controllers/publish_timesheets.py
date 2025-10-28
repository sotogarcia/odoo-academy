# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo.http import Controller, request, route
from odoo.tools.translate import _
from logging import getLogger
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

_logger = getLogger(__name__)


CURRENT_TEACH_URL = "/academy-timesheets/teacher/schedule"

TEACH_URL = "/academy-timesheets/teacher/<int:teacher_id>/schedule"
TEACH_ACT = (
    "academy_timesheets.action_report_academy_timesheets_primary_instructor"
)

STUDENT_URL = "/academy-timesheets/student/<int:student_id>/schedule"
STUDENT_ACT = "academy_timesheets.action_report_academy_timesheets_student"

EMBED_URL = "/academy-timesheets/training/<int:action_id>/schedule/embed"
ACTION_URL = "/academy-timesheets/training/<int:action_id>/schedule"
ACTION_ACT = (
    "academy_timesheets.action_report_academy_timesheets_training_action"
)

JSCRIPT = (
    '<script defer src="https://cdnjs.cloudflare.com/ajax/libs/'
    'iframe-resizer/4.3.6/iframeResizer.contentWindow.min.js" />'
)


class PublishTimesheets(Controller):
    """ """

    @route(CURRENT_TEACH_URL, type="http", auth="user", website=False)
    def publish_current_instructor_timesheet(self, **kw):
        kw = kw or {}

        doc_type = self._get_format_param(kw)
        target_date = self._compute_week_param(kw)
        download = self._get_download_param(kw)
        embed = self._get_embed_param(kw)

        allowed_xid = "academy_base.academy_group_consultant"
        if not request.env.user.has_group(allowed_xid):
            return request.not_found()

        uid = request.session.uid
        user_obj = request.env["res.users"]
        current_user = user_obj.browse(uid)

        domain = [("partner_id", "=", current_user.partner_id.id)]
        teacher_obj = request.env["academy.teacher"]
        teacher = teacher_obj.search(domain, limit=1)
        if not teacher:
            return request.not_found()

        content = self._render_report(
            TEACH_ACT, teacher, doc_type, target_date, embed
        )
        if not content:
            return request.not_found()

        return self._report_reponse(content, doc_type, download)

    @route(TEACH_URL, type="http", auth="user", website=False)
    def publish_instructor_timesheet(self, teacher_id, **kw):
        kw = kw or {}

        doc_type = self._get_format_param(kw)
        target_date = self._compute_week_param(kw)
        download = self._get_download_param(kw)
        embed = self._get_embed_param(kw)

        allowed_xid = "academy_base.academy_group_consultant"
        if not request.env.user.has_group(allowed_xid):
            return request.not_found()

        teacher_obj = request.env["academy.teacher"]
        teacher = teacher_obj.browse(teacher_id)
        if not teacher:
            return request.not_found()

        content = self._render_report(
            TEACH_ACT, teacher, doc_type, target_date, embed
        )
        if not content:
            return request.not_found()

        return self._report_reponse(content, doc_type, download)

    @route(STUDENT_URL, type="http", auth="user", website=False)
    def publish_student_timesheet(self, student_id, **kw):
        kw = kw or {}

        doc_type = self._get_format_param(kw)
        target_date = self._compute_week_param(kw)
        download = self._get_download_param(kw)
        embed = self._get_embed_param(kw)

        allowed_xid = "academy_base.academy_group_consultant"
        if not request.env.user.has_group(allowed_xid):
            return request.not_found()

        student_obj = request.env["academy.student"]
        student = student_obj.browse(student_id)
        if not student:
            return request.not_found()

        content = self._render_report(
            STUDENT_ACT, student, doc_type, target_date, embed
        )
        if not content:
            return request.not_found()

        return self._report_reponse(content, doc_type, download)

    @route(ACTION_URL, type="http", auth="public", website=False)
    def publish_training_action_timesheet(self, action_id, **kw):
        kw = kw or {}
        doc_type = self._get_format_param(kw)

        # Temporaty patch -> this will be removed
        if kw.get("week", "").lower() == "current":
            kw.pop("week")

        target_date = self._compute_week_param(kw)
        download = self._get_download_param(kw)
        embed = self._get_embed_param(kw)

        action_obj = request.env["academy.training.action"].sudo()
        action = action_obj.search([("id", "=", action_id)], limit=1)
        if not action:
            return request.not_found()

        content = self._render_report(
            ACTION_ACT, action, doc_type, target_date, embed
        )
        if not content:
            return request.not_found()

        return self._report_reponse(content, doc_type, download)

    @route(EMBED_URL, type="http", auth="public", website=False)
    def publish_embed_training_action_timesheet(self, action_id, **kw):
        kw = kw or {}
        doc_type = self._get_format_param(kw)

        # Temporaty patch -> this will be removed
        if kw.get("week", "").lower() == "current":
            kw.pop("week")

        target_date = self._compute_week_param(kw)
        download = self._get_download_param(kw)
        embed = self._get_embed_param(kw)

        action_obj = request.env["academy.training.action"].sudo()
        action = action_obj.search([("id", "=", action_id)], limit=1)
        if not action:
            return request.not_found()

        content = self._render_report(
            ACTION_ACT, action, doc_type, target_date, embed
        )
        if not content:
            return request.not_found()

        return self._report_reponse(content, doc_type, download)

    def _render_report(self, report_xid, record, doc_type, dt, embed=False):
        date_start, date_stop = self._weekly_interval(dt)

        datas = {
            "doc_ids": record.mapped("id"),
            "doc_model": getattr(record, "_name"),
            "interval": {"date_start": date_start, "date_stop": date_stop},
            "full_weeks": True,
        }

        if doc_type == "html":
            render_method_name = "_render_qweb_html"
        else:
            render_method_name = "_render_qweb_pdf"

        report_obj = request.env.ref(report_xid).sudo()
        render_method = getattr(report_obj, render_method_name)

        files = render_method(report_xid, [record.id], data=datas)
        content = files[0] if files and len(files[0]) else None

        if embed:
            if doc_type == "html":
                soup = BeautifulSoup(content, "html.parser")
                param_obj = request.env["ir.config_parameter"]
                url = param_obj.sudo().get_param("web.base.url")
                jscript = JSCRIPT.format(url)
                jscript = BeautifulSoup(jscript, "html.parser")
                soup.html.body.append(jscript)
                content = soup.prettify()
            else:
                msg = self.env._(
                    "iFrame Resizer can not be used with PDF files"
                )
                _logger.warning(msg)

        return content

    def _report_reponse(self, content, doc_type, download):
        if doc_type == "html":
            content_type = "text/html; charset=utf-8"
        else:
            doc_type = "pdf"  # Ensure valid value
            content_type = "application/pdf"

        if download:
            disposition = 'attachment; filename="Schedule.%s"' % doc_type
        else:
            disposition = "inline"

        pdfhttpheaders = [
            ("Content-Type", content_type),
            ("Content-Length", len(content)),
            ("Content-Disposition", disposition),
            (
                "Cache-Control",
                "no-cache, no-store, must-revalidate, max-age=0",
            ),
            ("Pragma", "no-cache"),
            ("Expires", "0"),
            ("Access-Control-Allow-Origin", "*"),
        ]

        return request.make_response(content, headers=pdfhttpheaders)

    def _get_format_param(self, kw):
        param = kw.get("format", False)

        if not param:
            param_name = "academy_timesheets.teacher_report_type"
            param_obj = request.env["ir.config_parameter"].sudo()
            param = param_obj.get_param(param_name)

        if not param or param not in ["html", "HTML", "pdf", "PDF"]:
            param = "html"

        return param.lower()

    def _compute_week_param(self, kw):
        """Returns a valid date for a day in a week. Week can be ``current``,
        ``last``, ``next`` or it can also be given as a date.

        Args:
            kw (dict): controller ``kw`` parameters

        Returns:
            datetime: valid datetime in the week
        """

        result = None

        date_str = kw.get("week", "").lower()
        if date_str:
            if date_str == "current":
                result = datetime.now()

            elif date_str == "next":
                result = datetime.now() + timedelta(days=7)

            elif date_str == "last":
                result = datetime.now() - timedelta(days=7)

            else:
                date_str = date_str.replace("/", "-")

                if len(date_str.split("-")[0]) == 4:
                    date_format = "%Y-%m-%d"
                else:
                    date_format = "%d-%m-%Y"

                try:
                    result = datetime.strptime(date_str, date_format)
                except Exception as ex:
                    _logger.warning(ex)

        if not result:
            result = datetime.now()
            # result = now.replace(hour=0, minute=0, second=0, microsecond=0)

            next_week_from = self._next_week_from()
            if next_week_from <= result:
                result -= timedelta(days=result.weekday())
                result += timedelta(days=8)

        return result

    def _next_week_from(self):
        weekdays = ["ISO5", "ISO6", "ISO7"]

        param_name = "academy_timesheets.schedule_for_next_week_from"
        param_obj = request.env["ir.config_parameter"].sudo()
        param_value = param_obj.get_param(param_name)

        if param_value and param_value in weekdays:
            offset = weekdays.index(param_value) + 4
        else:
            offset = 7  # Next monday

        dt = datetime.now()
        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        dt = dt - timedelta(days=dt.weekday()) + timedelta(days=offset)

        if offset < 7:
            param_name = "academy_timesheets.schedule_for_next_week_from_time"
            param_obj = request.env["ir.config_parameter"].sudo()
            param_value = param_obj.get_param(param_name)
            tm = self._safe_cast(param_value, float, 0.0)

            if tm:
                dt = dt + timedelta(seconds=tm * 3600.0)

        return dt

    @staticmethod
    def _safe_cast(val, to_type, default=None):
        """Performs a safe cast between `val` type to `to_type`"""

        try:
            return to_type(val)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _get_download_param(kw):
        param = kw.get("download", False)

        if not param:
            param_name = "academy_timesheets.teacher_report_download"
            param_obj = request.env["ir.config_parameter"].sudo()
            param = param_obj.get_param(param_name)
        else:
            param = param.lower() == "true"

        return bool(param)

    def _get_embed_param(self, kw):
        param = kw.get("embed", False)
        return self._safe_cast(param, bool, False)

    @classmethod
    def _weekly_interval(cls, dt):
        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        date_start = dt - timedelta(days=dt.weekday())
        date_stop = date_start + timedelta(days=6)

        return date_start, date_stop
