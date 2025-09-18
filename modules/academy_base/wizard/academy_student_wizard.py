# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from re import search
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.exceptions import UserError
from odoo.tools import safe_eval
from odoo.osv.expression import TRUE_DOMAIN, FALSE_DOMAIN
from ..utils.helpers import OPERATOR_MAP, one2many_count

from ..utils.record_utils import get_active_records, has_changed

from logging import getLogger
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

_logger = getLogger(__name__)


class AcademyStudentWizard(models.TransientModel):
    """Allow to perform massive actions over a student recordset"""

    _name = "academy.student.wizard"
    _description = "Academy student wizard"

    _rec_name = "id"
    _order = "id DESC"

    # -------------------------------------------------------------------------
    # Field: student_ids
    # -------------------------------------------------------------------------

    student_ids = fields.Many2many(
        string="Students",
        required=True,
        readonly=True,
        index=False,
        default=lambda self: self.default_student_ids(),
        help="Students on whom the action will be carried out",
        comodel_name="academy.student",
        relation="academy_student_wizard_student_rel",
        column1="wizard_id",
        column2="student_id",
        domain=[],
        context={},
    )

    def default_student_ids(self):
        """Retrieves a set of active students from the environment, supporting
        flexibility in handling different types of records related to students.

        Raises:
            UserError: If the active record set is neither 'academy.student'
                       and does not have any of the following attributes:
                       'student_id' or 'student_ids'.

        Returns:
            recordset: A recordset of student IDs, either directly from the
                       'academy.student' model or mapped from related records
                       in the active environment.
        """
        active_set = self.env["academy.student"]

        active_set = get_active_records(self.env)
        if active_set and active_set._name != "academy.student":
            if hasattr(active_set, "student_id"):
                active_set = active_set.mapped("student_id.id")
            elif hasattr(active_set, "student_ids"):
                active_set = active_set.mapped("student_ids.id")
            else:
                msg = _("Provided object «{}» has not students")
                raise UserError(msg.format(active_set._name))

        return active_set

    # -------------------------------------------------------------------------
    # Field: student_count
    # -------------------------------------------------------------------------

    student_count = fields.Integer(
        string="Student count",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help="Number of students on whom the action will be carried out",
        compute="_compute_student_count",
        search="_search_student_count",
    )

    @api.depends("student_ids")
    def _compute_student_count(self):
        counts = one2many_count(self, "student_ids")

        for record in self:
            record.student_count = counts.get(record.id, 0)

    @api.model
    def _search_student_count(self, operator, value):
        # Handle boolean-like searches Odoo may pass for required fields
        if value is True:
            return TRUE_DOMAIN if operator == "=" else FALSE_DOMAIN
        if value is False:
            return TRUE_DOMAIN if operator != "=" else FALSE_DOMAIN

        cmp_func = OPERATOR_MAP.get(operator)
        if not cmp_func:
            return FALSE_DOMAIN  # unsupported operator

        counts = one2many_count(self.search([]), "student_ids")
        matched = [cid for cid, cnt in counts.items() if cmp_func(cnt, value)]

        return [("id", "in", matched)] if matched else FALSE_DOMAIN

    # -------------------------------------------------------------------------
    # Field: action
    # -------------------------------------------------------------------------

    action = fields.Selection(
        string="Action",
        required=True,
        readonly=False,
        index=False,
        default=lambda self: self.default_action(),
        help="Action that will be carried out on the group of students",
        selection=lambda self: self.selection_values_for_action(),
    )

    def default_action(self):
        active_model = self.env.context.get("active_model", False)
        return "enrol" if active_model == "academy.student" else "unenroll"

    def selection_values_for_action(self):
        return [
            ("enrol", _("Enrol")),
            ("unenroll", _("Unenroll")),
            ("re_enroll", _("Re-enrol")),
            ("switch", _("Switch groups")),
            ("show", _("Show related records")),
        ]

    @api.onchange("action")
    def _onchange_action(self):
        if self.action in ("enrol", "re_enroll", "switch"):
            if self.action != "switch":
                self.current_training_action_id = None

            self.date_start = date.today()
            self.date_stop = None

        elif self.action in ("unenroll", "show"):
            self.joining_training_action_id = None

            self.date_start = None
            self.date_stop = date.today()

        else:
            self.target_student_ids = self.env["academy.student"]

    # -------------------------------------------------------------------------
    # Field: current_training_action_id
    # -------------------------------------------------------------------------

    current_training_action_id = fields.Many2one(
        string="Current training action",
        required=False,
        readonly=False,
        index=False,
        default=lambda self: self.default_current_training_action_id(),
        help="The group in which the student is currently enroled",
        comodel_name="academy.training.action",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    def default_current_training_action_id(self):
        result_set = self.env["academy.training.action"]

        expected = ["academy.training.action.enrolment"]
        enrolment_set = get_active_records(self.env, expected)

        if enrolment_set:
            training_action_set = enrolment_set.mapped("training_action_id")
            if training_action_set and len(training_action_set) == 1:
                result_set = training_action_set

        return result_set

    # -------------------------------------------------------------------------
    # Field: joining_interval_str
    # -------------------------------------------------------------------------

    current_interval_str = fields.Char(
        string="Current interval",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="current training action date start and date stop",
        size=50,
        translate=False,
        compute="_compute_current_interval_str",
    )

    @api.depends("current_training_action_id")
    def _compute_current_interval_str(self):
        for record in self:
            value = self._date_interval_str(record.current_training_action_id)
            record.current_interval_str = value

    def _date_interval_str(self, target):
        result = None

        if target:
            start = getattr(target, "start", False)

            if start:
                end = getattr(target, "end", False)

                if isinstance(start, datetime):
                    start = start.date()
                if isinstance(end, datetime):
                    end = end.date()

                start = fields.Date.to_string(start)
                end = fields.Date.to_string(end) if end else _("∞")

                result = "{} … {}".format(start, end)

        return result

    # -------------------------------------------------------------------------
    # Field: joining_training_action_id
    # -------------------------------------------------------------------------

    joining_training_action_id = fields.Many2one(
        string="Joining training action",
        required=False,
        readonly=False,
        index=False,
        default=None,
        help="The group that the student will join after the change",
        comodel_name="academy.training.action",
        domain=[],
        context={},
        ondelete="cascade",
        auto_join=False,
    )

    def _has_changed(self, field):
        result = False

        self.ensure_one()
        assert hasattr(
            self, field
        ), "Model {} does not have a field named {}".format(self._name, field)

        if self and self.origin:
            current_value = getattr(self, field, False)
            if current_value:
                old_value = getattr(self.origin, field, False)
                if old_value and current_value != old_value:
                    result = True

        return result

    @api.onchange("joining_training_action_id", "current_training_action_id")
    def _onchange_joining_training_action_id(self):
        if has_changed(self, "joining_training_action_id"):
            training_action = self.joining_training_action_id
        elif has_changed(self, "current_training_action_id"):
            training_action = self.current_training_action_id
        else:
            training_action = None

        if training_action:
            start = training_action.start.date()
            end = (training_action.end or datetime.max).date()

            if self.date_start:
                self.date_start = min(end, max(start, self.date_start))

            if self.date_stop:
                self.date_stop = max(start, min(end, self.end))

    # -------------------------------------------------------------------------
    # Field: joining_interval_str
    # -------------------------------------------------------------------------

    joining_interval_str = fields.Char(
        string="Joining interval",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help="Joining training action date start and date stop",
        size=50,
        translate=False,
        compute="_compute_joining_interval_str",
    )

    @api.depends("joining_training_action_id")
    def _compute_joining_interval_str(self):
        for record in self:
            value = self._date_interval_str(record.joining_training_action_id)
            record.joining_interval_str = value

    # -------------------------------------------------------------------------
    # Field: target_student_ids
    # -------------------------------------------------------------------------

    target_student_ids = fields.Many2many(
        string="Matched",
        required=True,
        readonly=False,
        index=False,
        default=None,
        help="Students on whom the action will be really carried out",
        comodel_name="academy.student",
        relation="academy_student_wizard_target_student_rel",
        column1="wizard_id",
        column2="student_id",
        domain=[],
        context={},
        compute="_compute_target_student_ids",
    )

    @api.depends(
        "student_ids",
        "action",
        "current_training_action_id",
        "joining_training_action_id",
        "date_start",
        "date_stop",
    )
    def _compute_target_student_ids(self):
        for record in self:
            if record.action == "enrol":
                record._compute_enroll_target_student_ids()
            elif record.action in "unenroll":
                record._compute_unenroll_target_student_ids()
            elif record.action == "re_enroll":
                record._compute_re_enroll_target_student_ids()
            elif record.action == "switch":
                record._compute_switch_target_student_ids()
            elif record.action == "show":
                record._compute_show_target_student_ids()
            else:
                record.target_student_ids = [(5, 0, 0)]

    def _compute_enroll_target_student_ids(self):
        self.ensure_one()

        joining_id = self.joining_training_action_id

        if joining_id and self.date_start:
            point_in_time = self.compute_point_in_time(
                self.date_start, self.date_stop or date.max
            )
            enrolled_set = self.student_ids.fetch_enrolled(
                joining_id, point_in_time, False
            )

            student_ids = self.student_ids.ids
            enrolled_ids = enrolled_set.ids
            ids = [item for item in student_ids if item not in enrolled_ids]

            self.target_student_ids = [(6, 0, ids)]
        else:
            self.target_student_ids = [(5, 0, 0)]

    def _compute_unenroll_target_student_ids(self):
        self.ensure_one()
        current_id = self.current_training_action_id

        if current_id:
            enrolled_set = self.student_ids.fetch_enrolled(
                current_id, date.today(), False
            )

            self.target_student_ids = [(6, 0, enrolled_set.ids)]
        else:
            self.target_student_ids = [(5, 0, 0)]

    def _compute_re_enroll_target_student_ids(self):
        self.ensure_one()

        joining_id = self.joining_training_action_id

        if joining_id and self.date_start:
            point_in_time = self.compute_point_in_time(
                self.date_start, self.date_stop or date.max
            )

            ever_enrolled_set = self.student_ids.fetch_enrolled(
                joining_id, None, True
            )
            enrolled_set = self.student_ids.fetch_enrolled(
                joining_id, point_in_time, False
            )

            ever_ids = ever_enrolled_set.ids
            enrolled_ids = enrolled_set.ids
            ids = [item for item in ever_ids if item not in enrolled_ids]

            self.target_student_ids = [(6, 0, ids)]
        else:
            self.target_student_ids = [(5, 0, 0)]

    def _compute_switch_target_student_ids(self):
        self.ensure_one()

        joining_id = self.joining_training_action_id
        current_id = self.current_training_action_id

        if current_id and joining_id and self.date_start:
            point_in_time = self.compute_point_in_time(
                self.date_start, self.date_stop or date.max
            )

            current_set = self.student_ids.fetch_enrolled(
                current_id, date.today(), False
            )
            enrolled_set = self.student_ids.fetch_enrolled(
                joining_id, point_in_time, False
            )

            current_ids = current_set.ids
            enrolled_ids = enrolled_set.ids
            ids = [item for item in current_ids if item not in enrolled_ids]

            self.target_student_ids = [(6, 0, ids)]
        else:
            self.target_student_ids = [(5, 0, 0)]

    def _compute_show_target_student_ids(self):
        self.ensure_one()
        current_id = self.current_training_action_id

        if current_id:
            point_in_time = self.compute_point_in_time(
                self.date_start, self.date_stop or date.max
            )
            enrolled_set = self.student_ids.fetch_enrolled(
                current_id, point_in_time, False
            )
            self.target_student_ids = [(6, 0, enrolled_set.ids)]
        else:
            self.target_student_ids = [(5, 0, 0)]

    # -------------------------------------------------------------------------
    # Field: target_student_count
    # -------------------------------------------------------------------------

    target_student_count = fields.Integer(
        string="Matched count",
        required=True,
        readonly=True,
        index=False,
        default=0,
        help="Number of students actually impacted by the action",
        compute="_compute_target_student_count",
    )

    @api.depends("target_student_ids")
    def _compute_target_student_count(self):
        for record in self:
            record.target_student_count = len(record.target_student_ids)

    # -------------------------------------------------------------------------
    # Field: date_start
    # -------------------------------------------------------------------------

    date_start = fields.Date(
        string="Enrolment date",
        required=False,
        readonly=False,
        index=False,
        default=lambda self: self.default_date_start(),
        help="Subscription date will be used for the new enrollments",
    )

    def default_date_start(self):
        return date.today()

    # -------------------------------------------------------------------------
    # Field: date_stop
    # -------------------------------------------------------------------------

    date_stop = fields.Date(
        string="Drop date",
        required=False,
        readonly=False,
        index=False,
        default=lambda self: self.default_date_stop(),
        help="Unsubscription date will be used for the new enrollments",
    )

    def default_date_stop(self):
        return date.today().replace(day=1) + relativedelta(months=1)

    # -------------------------------------------------------------------------
    # Field: description
    # -------------------------------------------------------------------------

    description = fields.Text(
        string="Description",
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=(
            "Description of the action that will be carried out on the "
            "selected students"
        ),
        translate=True,
        compute="_compute_description",
    )

    @api.depends("action")
    def _compute_description(self):
        name_pattern = "academy_interface_student_wizard_action_{}"
        module = "academy_base"

        help_obj = self.env["academy.interface.help.string"]

        for record in self:
            if record.action:
                name = name_pattern.format(record.action)
                record.description = help_obj.get_by_ref([module, name])
            else:
                record.description = _(
                    "Choose an action to perform on selected students"
                )

    # -------------------------------------------------------------------------
    # Button: perform action. Main method: perform_action
    # -------------------------------------------------------------------------

    def _perform_action_enroll(self):
        self.ensure_one()

        enrolment_obj = self.env["academy.training.action.enrolment"]

        date_start, date_stop = self.date_start, self.date_stop
        # excluded_set = self._get_excluded_students()

        # Create new enrolments
        values = {
            "student_id": None,
            "training_action_id": self.joining_training_action_id.id,
            "register": date_start.strftime(DATE_FORMAT),
            "deregister": date_stop and date_stop.strftime(DATE_FORMAT),
            "active": True,
        }

        for student in self.target_student_ids:
            values.update(student_id=student.id)
            enrolment_obj.create(values)

        # # Update previously existing enrolments
        # #       Interval
        # #    ╠════════════╣
        # # |-----|->
        # #     <-|-----|->
        # #           <-|---<-|
        # # |---------------<-|

        # point_in_time = self.compute_point_in_time(date_start, date_stop)

        # enrolment_set = enrolment_obj.fetch_enrollments(
        #     excluded_set, self.joining_training_action_id, point_in_time)

        # values = {'deregister': values.pop('deregister')}
        # for enrolment in enrolment_set:
        #     lbound = min(date_start, enrolment.register)
        #     values['register'] = lbound.strftime(DATE_FORMAT)
        #     enrolment_set.write(values)

    def _perform_action_unenroll(self):
        self.ensure_one()

        enrolment_obj = self.env["academy.training.action.enrolment"]

        today = date.today()
        date_stop = self.date_stop or today

        enrolment_set = enrolment_obj.fetch_enrollments(
            self.target_student_ids, self.current_training_action_id, today
        )

        enrolment_set.write(
            {"deregister": date_stop and date_stop.strftime(DATE_FORMAT)}
        )

    def _perform_action_re_enroll(self):
        self.ensure_one()

        joining_action_id = self.joining_training_action_id.id
        date_start = self.date_start.strftime(DATE_FORMAT)
        if self.date_stop:
            date_stop = self.date_stop.strftime(DATE_FORMAT)
        else:
            date_stop = None
        today = date.today().strftime(DATE_FORMAT)

        enrolment_obj = self.env["academy.training.action.enrolment"]

        for student in self.target_student_ids:
            domain = [
                "&",
                "&",
                ("student_id", "=", student.id),
                ("training_action_id", "=", joining_action_id),
                ("deregister", "<=", today),
            ]

            enrolment = enrolment_obj.search(
                domain, order="deregister DESC", limit=1
            )

            enrolment.copy({"register": date_start, "deregister": date_stop})

    def _perform_action_enroll_switch(self):
        self.ensure_one()

        date_start, date_stop = self.date_start, self.date_stop
        target_student_set = self.target_student_ids

        enrolment_obj = self.env["academy.training.action.enrolment"]

        # Unenroll from old trainng action
        enrolment_set = enrolment_obj.fetch_enrollments(
            target_student_set, self.current_training_action_id, date_start
        )
        enrolment_set.write({"deregister": date_start.strftime(DATE_FORMAT)})

        excluded_set = self._get_excluded_students()

        # Common values will be used with switched and non switched students
        values = {
            "student_id": None,
            "training_action_id": self.joining_training_action_id.id,
            "register": date_start.strftime(DATE_FORMAT),
            "deregister": date_stop and date_stop.strftime(DATE_FORMAT),
            "active": True,
        }

        # Create new enrolments to switched students
        for student in target_student_set:
            values.update(student_id=student.id)
            enrolment_obj.create(values)

        # Create new enrolments to non switched students
        for student in excluded_set:
            values.update(student_id=student.id)
            enrolment_obj.create(values)

    def _perform_action_show(self):
        self.ensure_one()

        ENROLMENT_MODEL = "academy.training.action.enrolment"

        active_model = self.env.context.get("active_model", False)
        if active_model == ENROLMENT_MODEL:
            model_name = _("students")
            action_xid = "academy_base.action_student_act_window"
            target_set = self.target_student_ids

        elif active_model == "academy.student":
            model_name = _("training action enrollments")
            action_xid = (
                "academy_base.action_training_action_enrolment_act_window"
            )

            enrolment_obj = self.env[ENROLMENT_MODEL]

            point_in_time = self.compute_point_in_time(
                self.date_start, self.date_stop or date.max
            )

            target_set = enrolment_obj.fetch_enrollments(
                self.target_student_ids,
                self.current_training_action_id,
                point_in_time,
            )

        if target_set:
            result = self._build_action_to_show_records(action_xid, target_set)
        else:
            result = self._build_action_to_notify_no_records(model_name)

        return result

    @api.model
    def _build_action_to_show_records(self, action_xid, targets):
        domain = [("id", "in", targets.ids)]

        act_wnd = self.env.ref(action_xid)

        context = self.env.context.copy()
        context.update(safe_eval(act_wnd.context))

        context.pop("search_default_in_progress", False)
        context.pop("search_default_enrolled", False)

        serialized = {
            "type": "ir.actions.act_window",
            "res_model": act_wnd.res_model,
            "target": "current",
            "name": act_wnd.name,
            "view_mode": act_wnd.view_mode,
            "domain": domain,
            "context": context,
            "search_view_id": act_wnd.search_view_id.id,
            "help": act_wnd.help,
        }

        return serialized

    @staticmethod
    def _build_action_to_notify_no_records(model):
        message = _("No matching {model} found for the indicated criteria")

        serialized = {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("No matching records"),
                "message": message,
                "type": "info",  # types: success, warning, danger, info
                "sticky": True,  # True/False will display for few seconds
            },
        }

        return serialized

    def _perform_action(self):
        if self.action == "enrol":
            result = self._perform_action_enroll()
        elif self.action == "unenroll":
            result = self._perform_action_unenroll()
        elif self.action == "re_enroll":
            result = self._perform_action_re_enroll()
        elif self.action == "switch":
            result = self._perform_action_enroll_switch()
        elif self.action == "show":
            result = self._perform_action_show()
        else:
            result = False

        return result

    def perform_action(self):
        for record in self:
            result = record._perform_action()

        return result if len(record) == 1 else bool(record)

    # -------------------------------------------------------------------------
    # Others
    # -------------------------------------------------------------------------

    def _get_excluded_students(self):
        """Retrieves records of selected but non-target students

        IMPORTANT: This method must be called before perform changes in
        enrolments.

        Returns:
            models.Model: selected but non-target students

        """
        self.ensure_one()

        full_set = self.student_ids
        target_set = self.target_student_ids

        return full_set.filtered(lambda student: student not in target_set)

    @staticmethod
    def compute_point_in_time(date_start, date_stop):
        if date_start and date_stop:
            point_in_time = (date_start, date_stop)
        elif date_start:
            point_in_time = date_start
        elif date_stop:
            point_in_time = date_stop
        else:
            point_in_time = date.today()

        return point_in_time
