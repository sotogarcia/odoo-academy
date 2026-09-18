###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################


from odoo import http
from odoo.http import request

ROUTE_PROGRAM = "/academy/catalog/program/<int:program_id>"
ROUTE_ACTION = "/academy/monitoring/action/<int:action_id>"


class Publish(http.Controller):
    @http.route(
        ROUTE_PROGRAM,
        type="http",
        auth="user",
        methods=["GET"],
        readonly=True,
    )
    def program(self, program_id):
        """Render training program catalog page using QWeb report."""
        program_obj = request.env["academy.training.program"]
        program = program_obj.browse(program_id).exists()
        if not program:
            raise request.not_found()

        view_name = "academy_base.view_academy_training_program_modules_qweb"
        values = {"docs": program}
        html = request.env["ir.ui.view"]._render_template(
            view_name,
            values,
        )

        headers = [("Content-Type", "text/html; charset=utf-8")]
        return request.make_response(html, headers=headers)

    @http.route(
        ROUTE_ACTION,
        type="http",
        auth="user",
        methods=["GET"],
        readonly=True,
    )
    def action(self, action_id):
        """Render training action catalog page using QWeb report."""
        action_obj = request.env["academy.training.action"]
        action = action_obj.browse(action_id).exists()
        if not action:
            raise request.not_found()

        view_name = "academy_base.view_academy_training_action_modules_qweb"
        values = {"docs": action}
        html = request.env["ir.ui.view"]._render_template(
            view_name,
            values,
        )

        headers = [("Content-Type", "text/html; charset=utf-8")]
        return request.make_response(html, headers=headers)
