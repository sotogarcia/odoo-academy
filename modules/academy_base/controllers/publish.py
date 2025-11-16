# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request, Response

import logging

_logger = logging.getLogger(__name__)


class Publish(http.Controller):
    @http.route(
        "/academy/catalog/program/<program_id>", type="http", auth="public"
    )
    def program(self, **kw):
        """Render training program catalog page using QWeb report."""
        program_raw = kw.get("program_id")
        try:
            program_id = int(program_raw)
        except (TypeError, ValueError):
            return request.not_found()

        program_obj = request.env["academy.training.program"]
        program = program_obj.browse(program_id).exists()
        if not program:
            return request.not_found()

        view_name = "academy_base.view_academy_training_program_modules_qweb"
        values = {"docs": program}
        html = request.env["ir.ui.view"]._render_template(
            view_name,
            values,
        )

        headers = [("Content-Type", "text/html; charset=utf-8")]
        return request.make_response(html, headers=headers)

    @http.route(
        "/academy/monitoring/action/<action_id>", type="http", auth="public"
    )
    def action(self, **kw):
        """Render training action catalog page using QWeb report."""
        action_raw = kw.get("action_id")
        try:
            action_id = int(action_raw)
        except (TypeError, ValueError):
            return request.not_found()

        action_obj = request.env["academy.training.action"]
        action = action_obj.browse(action_id).exists()
        if not action:
            return request.not_found()

        view_name = "academy_base.view_academy_training_action_modules_qweb"
        values = {"docs": action}
        html = request.env["ir.ui.view"]._render_template(
            view_name,
            values,
        )

        headers = [("Content-Type", "text/html; charset=utf-8")]
        return request.make_response(html, headers=headers)
