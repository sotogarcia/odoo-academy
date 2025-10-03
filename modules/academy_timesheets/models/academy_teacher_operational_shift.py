# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools import drop_view_if_exists, safe_eval

from logging import getLogger


_logger = getLogger(__name__)


class AcademyTeacherOperationalShift(models.Model):
    """
    Model for managing the operational shifts of academy teachers.

    This model is used to track and organize the various shifts or
    time periods during which academy teachers conduct their activities.
    These activities can include teaching sessions, administrative duties,
    or other related tasks. The model facilitates the scheduling and
    oversight of teachers' operational shifts, ensuring effective time
    management and allocation of teaching resources within the academy.
    """

    _name = "academy.teacher.operational.shift"
    _description = "Teacher Operational Shift Management"

    _rec_name = "id"
    _order = "date_start ASC, date_stop ASC"

    _auto = False
    _table = "academy_teacher_operational_shift"

    _check_company_auto = True

    company_id = fields.Many2one(
        string="Company",
        required=True,
        readonly=True,
        index=True,
        default=None,
        help=(
            "Identifier of the company to which this operational shift "
            "belongs. Each shift is linked to a specific company within "
            "the academy"
        ),
        comodel_name="res.company",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        aggregator="count",
    )

    teacher_id = fields.Many2one(
        string="Teacher",
        required=True,
        readonly=True,
        index=True,
        default=None,
        help=(
            "Reference to the academy teacher associated with this "
            "operational shift. This field links the shift to a specific "
            "teacher record"
        ),
        comodel_name="academy.teacher",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
        aggregator="count",
    )

    date_start = fields.Datetime(
        string="Date start",
        required=True,
        readonly=True,
        index=True,
        default=fields.datetime.now(),
        help=(
            "The start date and time of the operational shift. Indicates "
            "when the teacher's period of activity begins"
        ),
        aggregator="min",
    )

    date_stop = fields.Datetime(
        string="Date stop",
        required=True,
        readonly=True,
        index=True,
        default=fields.datetime.now(),
        help=(
            "The end date and time of the operational shift. Specifies when "
            "the teacher's period of activity concludes"
        ),
        aggregator="max",
    )

    date_delay = fields.Float(
        string="Duration",
        required=True,
        readonly=False,
        index=False,
        default=0.0,
        digits=(16, 2),
        help=(
            "Specifies the duration of the operational shift in hours. "
            "This field represents the total time length for the shift, "
            "calculated as the difference between the start and end times. "
            "It is useful for assessing the duration of a teacher's "
            "activities during the shift"
        ),
        aggregator="sum",
    )

    session_count = fields.Integer(
        string="Session count",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help=(
            "Total number of sessions or activities conducted during this "
            "operational shift. This field can be used for tracking and "
            "analyzing the teacher's workload"
        ),
        aggregator="sum",
    )

    session_ids = fields.Many2many(
        string="Sessions",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Sessions involved in this shift",
        comodel_name="academy.training.session",
        relation="academy_teacher_operation_shift_training_session_rel",
        column1="shift_id",
        column2="session_id",
        domain=[],
        context={},
        compute="_compute_session_ids",
    )

    @api.depends("teacher_id", "company_id", "date_start", "date_stop")
    def _compute_session_ids(self):
        teacher_key = "teacher_assignment_ids.teacher_id"

        for record in self:
            date_start = fields.Datetime.to_string(record.date_start)
            date_stop = fields.Datetime.to_string(record.date_stop)

            session_domain = [
                (teacher_key, "=", record.teacher_id.id),
                ("company_id", "=", record.company_id.id),
                ("date_start", ">=", date_start),
                ("date_stop", "<=", date_stop),
                ("state", "=", "ready"),
            ]
            session_obj = self.env["academy.training.session"]
            record.session_ids = session_obj.search(session_domain)

    def init(self):
        sentence = "CREATE or REPLACE VIEW {} as ( {} )"

        drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute(sentence.format(self._table, self._view_sql))

        self.prevent_actions()

    def prevent_actions(self):
        actions = ["INSERT", "UPDATE", "DELETE"]

        BASE_SQL = """
            CREATE OR REPLACE RULE {table}_{action} AS
                ON {action} TO {table} DO INSTEAD NOTHING
        """

        for action in actions:
            sql = BASE_SQL.format(table=self._table, action=action)
            self.env.cr.execute(sql)

    _view_sql = """
        WITH session_changes AS (
            SELECT
                sess."id" AS session_id,
                sess.company_id,
                teach."id" AS teacher_id,
                sess.date_start,
                sess.date_stop,
                CASE
                    WHEN
                        LAG(sess.date_stop) OVER (
                            PARTITION BY sess.company_id, teach."id"
                            ORDER BY sess.date_start
                        ) = sess.date_start
                    THEN FALSE
                    ELSE TRUE
                END AS is_new_group,
                sess.create_date,
                sess.write_date
            FROM
                academy_training_session AS sess
            INNER JOIN academy_training_session_teacher_rel AS rel
                ON rel.session_id = sess.id
                AND sess.active
                AND sess.state = 'ready'
            INNER JOIN academy_teacher AS teach
                ON teach.id = rel.teacher_id

            -- BEGIN: Compute information only from last n days
            LEFT JOIN ir_config_parameter AS icp
                ON icp."key" = 'academy_timesheets.teacher_shift_lookback_days'
            WHERE sess.date_start >= (
                CURRENT_DATE - (
                    COALESCE(icp."value"::VARCHAR, '45'::VARCHAR)::VARCHAR
                    || ' days'
                )::INTERVAL
            )::TIMESTAMP(0)
            -- END: Compute information from last n days
        ),
        grouped_sessions AS (
            SELECT
                *,
                SUM(CASE WHEN is_new_group THEN 1 ELSE 0 END) OVER (
                    PARTITION BY company_id, teacher_id
                    ORDER BY date_start
                ) AS group_id
            FROM
                session_changes
        ),
        teacher_shifts AS (
            SELECT
                ROW_NUMBER() OVER()::INTEGER AS "id",
                MIN(gs.create_date) AS create_date,
                MAX(gs.write_date) AS write_date,
                MIN(date_start) AS date_start,
                MAX(date_stop) AS date_stop,
                COUNT(*) AS session_count,
                company_id,
                teacher_id
            FROM
                grouped_sessions AS gs
            INNER JOIN academy_teacher AS teach
                ON teach."id" = gs.teacher_id
            GROUP BY
                company_id,
                teacher_id,
                group_id
            ORDER BY
                company_id,
                teacher_id,
                date_start,
                date_stop
        )
        SELECT
            ts.*,
            (
                EXTRACT(EPOCH FROM AGE(date_stop, date_start)) / 3600
            )::FLOAT AS date_delay,
            1::INTEGER AS create_uid,
            1::INTEGER AS write_uid
        FROM teacher_shifts AS ts
        INNER JOIN academy_teacher AS teach  ON teach."id" = ts.teacher_id
    """

    @api.depends("teacher_id", "company_id")
    @api.depends_context("lang")
    def _compute_display_name(self):
        for record in self:
            if isinstance(record.id, models.NewId):
                text = self.env._("New operational shift")
            else:
                text = f"{record.teacher_id.name} - {record.company_id.name}"

            record.display_name = text

    def view_sessions(self):
        self.ensure_one()

        action_xid = "academy_timesheets.action_sessions_act_window"
        act_wnd = self.env.ref(action_xid)

        name = self.env._("Sessions involved")

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))

        domain = [("id", "in", self.session_ids.ids)]

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": act_wnd.res_model,
            "target": "current",
            "name": name,
            "view_mode": act_wnd.view_mode,
            "domain": domain,
            "context": context,
            "search_view_id": act_wnd.search_view_id.id,
            "help": act_wnd.help,
        }

        return serialized
