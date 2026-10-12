###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

"""ADR-05: academic sign-up state transitions provided by academy_base.

Run against academy_base without academy_sale_invoice installed. The tests
verify the agreed target implementation, including initial synchronization
on academy.student.signup.create() and the signup_date write trigger.

The local-day helper res.company.local_day_bounds_to_utc() must be present.
"""

from contextlib import contextmanager
from datetime import date, datetime, time, timedelta, timezone as dt_timezone
from unittest.mock import patch

from pytz import UTC, timezone

from odoo import fields
from odoo.tests.common import TransactionCase


# ruff: noqa: DTZ001
class TestStudentSignupStateBase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company
        cls.company.partner_id.tz = "UTC"
        cls.company.auto_signup = False

        cls.signup_obj = cls.env["academy.student.signup"]
        cls.student_obj = cls.env["academy.student"]
        cls.enrolment_obj = cls.env["academy.training.action.enrolment"]
        cls.transition_obj = cls.env["academy.student.signup.state.transition"]

        # Follow the fixture convention already used by academy_base tests.
        cls.source_action = cls.env.ref(
            "academy_base.academy_training_action_demo_1_default"
        )
        cls.training_modality = cls.env.ref(
            "academy_base.academy_training_modality_classroom"
        )

    def setUp(self):
        super().setUp()
        self.today = datetime.now(dt_timezone.utc).date()

    # -- Fixtures --------------------------------------------------------------

    def _create_signup(self, signup_day=None):
        if signup_day is None:
            signup_day = self.today - timedelta(days=2)

        student = self.student_obj.create(
            {"name": "ADR-05 base state student"}
        )

        return self.signup_obj.create(
            {
                "student_id": student.id,
                "company_id": self.company.id,
                "signup_date": datetime.combine(signup_day, time(8)),
            }
        )

    def _create_action(self):
        return self.source_action.with_company(self.company).copy(
            {
                "parent_id": False,
                "company_id": self.company.id,
                "date_start": datetime.combine(
                    self.today - timedelta(days=30), time(8)
                ),
                "date_stop": datetime.combine(
                    self.today + timedelta(days=30), time(22)
                ),
                "seats": 10,
                "excess": 10,
                "allow_excess": True,
            }
        )

    def _create_enrolment(
        self,
        signup,
        register_day=None,
        deregister_day=None,
        active=True,
    ):
        if register_day is None:
            register_day = self.today - timedelta(days=1)
        if deregister_day is None:
            deregister_day = self.today + timedelta(days=2)

        action = self._create_action()

        return self.enrolment_obj.create(
            {
                "student_id": signup.student_id.id,
                "signup_id": signup.id,
                "training_action_id": action.id,
                "training_modality_id": self.training_modality.id,
                "full_enrolment": False,
                "state": "joined",
                "register": datetime.combine(register_day, time(10)),
                "deregister": datetime.combine(deregister_day, time(18)),
                "active": active,
            }
        )

    def _transitions(self, signup):
        return self.transition_obj.search(
            [("signup_id", "=", signup.id)],
            order="timestamp ASC, id ASC",
        )

    def _assert_states(self, signup, states):
        self.assertEqual(self._transitions(signup).mapped("state"), states)
        self.assertEqual(signup.state, states[-1])

    @staticmethod
    def _local_day_bounds(local_day, tz_name):
        tz = timezone(tz_name)
        start = tz.localize(datetime.combine(local_day, time.min))
        stop = tz.localize(
            datetime.combine(local_day + timedelta(days=1), time.min)
        )
        return (
            start.astimezone(UTC).replace(tzinfo=None),
            stop.astimezone(UTC).replace(tzinfo=None),
        )

    @contextmanager
    def _at_local_day(self, local_day):
        """Control only the company's day boundaries, not the state rules."""
        company_class = type(self.company)
        original = company_class.local_day_bounds_to_utc
        company_id = self.company.id

        def local_day_bounds_to_utc(company):
            if company.id == company_id:
                return self._local_day_bounds(
                    local_day, company.partner_id.tz or "UTC"
                )
            return original(company)

        with patch.object(
            company_class,
            "local_day_bounds_to_utc",
            local_day_bounds_to_utc,
        ):
            yield

    # -- Creation and initial history -----------------------------------------

    def test_create_signup_registers_initial_signed_up(self):
        signup = self._create_signup(signup_day=self.today)
        transitions = self._transitions(signup)

        self.assertEqual(signup.state, "signed_up")
        self.assertEqual(len(transitions), 1)
        self.assertEqual(transitions.state, "signed_up")
        self.assertFalse(transitions.previous_state)
        self.assertFalse(transitions.source_ref)
        self.assertTrue(transitions.timestamp)

    def test_create_multiple_signups_registers_each_initial_history(self):
        students = self.student_obj.create(
            [{"name": "ADR-05 batch A"}, {"name": "ADR-05 batch B"}]
        )
        signups = self.signup_obj.create(
            [
                {
                    "student_id": student.id,
                    "company_id": self.company.id,
                    "signup_date": datetime.combine(self.today, time(8)),
                }
                for student in students
            ]
        )

        self.assertEqual(len(signups), 2)
        for signup in signups:
            self._assert_states(signup, ["signed_up"])

    # -- Academic coverage ----------------------------------------------------

    def test_effective_enrolment_creates_enrolled_transition(self):
        signup = self._create_signup()
        enrolment = self._create_enrolment(signup)

        self._assert_states(signup, ["signed_up", "enrolled"])
        self.assertEqual(self._transitions(signup)[-1].source_ref, enrolment)
        self.assertEqual(
            self._transitions(signup)[-1].previous_state, "signed_up"
        )

    def test_future_enrolment_does_not_yet_provide_coverage(self):
        signup = self._create_signup()
        self._create_enrolment(
            signup,
            register_day=self.today + timedelta(days=2),
            deregister_day=self.today + timedelta(days=5),
        )

        self._assert_states(signup, ["signed_up"])

    def test_enrolment_ending_today_covers_entire_local_day(self):
        signup = self._create_signup()
        self._create_enrolment(signup, deregister_day=self.today)

        self._assert_states(signup, ["signed_up", "enrolled"])

        with self._at_local_day(self.today):
            signup.synchronize_state_transitions()

        self._assert_states(signup, ["signed_up", "enrolled"])

    def test_next_local_day_returns_to_signed_up_without_retention(self):
        signup = self._create_signup()
        self._create_enrolment(signup, deregister_day=self.today)

        with self._at_local_day(self.today + timedelta(days=1)):
            signup.synchronize_state_transitions()

        self._assert_states(signup, ["signed_up", "enrolled", "signed_up"])
        self.assertFalse(self._transitions(signup)[-1].source_ref)

    def test_archiving_last_enrolment_removes_academic_coverage(self):
        signup = self._create_signup()
        enrolment = self._create_enrolment(signup)
        enrolment.write({"active": False})

        self._assert_states(signup, ["signed_up", "enrolled", "signed_up"])

    # -- Historic traceability ------------------------------------------------

    def test_deleting_referenced_enrolment_preserves_history(self):
        signup = self._create_signup()
        enrolment = self._create_enrolment(signup)
        enrolled_transition = self._transitions(signup)[-1]
        enrolled_transition_id = enrolled_transition.id

        self.env.cr.execute(
            """
            SELECT source_ref
            FROM academy_student_signup_state_transition
            WHERE id = %s
            """,
            (enrolled_transition_id,),
        )
        original_source = self.env.cr.fetchone()[0]
        self.assertEqual(
            original_source,
            f"academy.training.action.enrolment,{enrolment.id}",
        )

        enrolment.unlink()

        self.assertTrue(self.transition_obj.browse(enrolled_transition_id).exists())
        self.env.cr.execute(
            """
            SELECT source_ref
            FROM academy_student_signup_state_transition
            WHERE id = %s
            """,
            (enrolled_transition_id,),
        )
        self.assertEqual(self.env.cr.fetchone()[0], original_source)
        self._assert_states(signup, ["signed_up", "enrolled", "signed_up"])

    def test_second_synchronization_without_changes_is_idempotent(self):
        signup = self._create_signup()
        self._create_enrolment(signup)
        previous_ids = self._transitions(signup).ids

        self.assertFalse(signup.synchronize_state_transitions())
        self.assertEqual(self._transitions(signup).ids, previous_ids)
        self.assertEqual(signup.state, "enrolled")

    def test_sync_on_multiple_signups_keeps_histories_separate(self):
        signup_a = self._create_signup()
        signup_b = self._create_signup()
        self._create_enrolment(signup_a)
        self._create_enrolment(signup_b)

        (signup_a | signup_b).synchronize_state_transitions()

        self._assert_states(signup_a, ["signed_up", "enrolled"])
        self._assert_states(signup_b, ["signed_up", "enrolled"])

    # -- Update triggers and calendar boundaries -------------------------------

    def test_changing_signup_date_triggers_synchronization(self):
        signup = self._create_signup()
        signup_class = type(signup)
        original = signup_class.synchronize_state_transitions
        calls = []

        def sync_and_record(signups, *args, **kwargs):
            calls.extend(signups.ids)
            return original(signups, *args, **kwargs)

        with patch.object(
            signup_class,
            "synchronize_state_transitions",
            sync_and_record,
        ):
            signup.write(
                {
                    "signup_date": datetime.combine(
                        self.today - timedelta(days=1), time(8)
                    )
                }
            )

        self.assertIn(signup.id, calls)
        self._assert_states(signup, ["signed_up"])

    def test_state_write_does_not_trigger_recursive_synchronization(self):
        signup = self._create_signup()
        signup_class = type(signup)
        original = signup_class.synchronize_state_transitions
        calls = []

        def sync_and_record(signups, *args, **kwargs):
            calls.extend(signups.ids)
            return original(signups, *args, **kwargs)

        with patch.object(
            signup_class,
            "synchronize_state_transitions",
            sync_and_record,
        ):
            signup.write({"state": "signed_up"})

        self.assertFalse(calls)

    def test_local_day_boundaries_respect_daylight_saving_time(self):
        self.company.partner_id.tz = "Europe/Madrid"

        cases = [
            (date(2026, 3, 29), 23),
            (date(2026, 10, 25), 25),
        ]

        for local_day, expected_hours in cases:
            with self.subTest(day=local_day):
                with patch.object(
                    fields.Date, "context_today", return_value=local_day
                ):
                    start_utc, end_utc = (
                        self.company.local_day_bounds_to_utc()
                    )

                self.assertIsNone(start_utc.tzinfo)
                self.assertIsNone(end_utc.tzinfo)
                self.assertEqual(
                    (end_utc - start_utc).total_seconds() / 3600,
                    expected_hours,
                )
