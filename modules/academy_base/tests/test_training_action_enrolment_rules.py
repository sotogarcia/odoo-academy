from datetime import datetime, timedelta

from lxml import etree

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


# ruff: noqa: DTZ001
class TestTrainingActionEnrolmentRules(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.enrolment_obj = cls.env["academy.training.action.enrolment"]
        cls.signup_obj = cls.env["academy.student.signup"]

        cls.source_action = cls.env.ref(
            "academy_base.academy_training_action_demo_1_default"
        )
        cls.training_modality = cls.env.ref(
            "academy_base.academy_training_modality_classroom"
        )

        cls.test_students = cls.env["academy.student"].create(
            [
                {"name": "Enrolment rules test student 1"},
                {"name": "Enrolment rules test student 2"},
                {"name": "Enrolment rules test student 3"},
                {"name": "Enrolment rules test student 4"},
            ]
        )

        signup_date = datetime(2020, 1, 1, 8, 0)
        test_signups = []

        for student in cls.test_students:
            domain = [
                ("student_id", "=", student.id),
                ("company_id", "=", cls.env.company.id),
            ]
            signup = cls.signup_obj.search(domain, limit=1)

            if signup:
                signup.write({"signup_date": signup_date})
            else:
                signup = cls.signup_obj.create(
                    {
                        "student_id": student.id,
                        "company_id": cls.env.company.id,
                        "signup_code": cls.signup_obj._next_signup_code(
                            cls.env.company.id
                        ),
                        "signup_date": signup_date,
                    }
                )

            test_signups.append(signup)

        (
            cls.signup_1,
            cls.signup_2,
            cls.signup_3,
            cls.signup_4,
        ) = test_signups

    # -- Helpers ---------------------------------------------------------------

    def _create_action(
        self,
        seats=2,
        excess=None,
        allow_excess=False,
        date_start=None,
        date_stop=None,
        open_ended=False,
    ):
        if excess is None:
            excess = seats

        date_start = date_start or datetime(2026, 1, 1, 8, 0)

        if open_ended:
            date_stop = False
        elif date_stop is None:
            date_stop = datetime(2026, 12, 31, 22, 0)

        return self.source_action.copy(
            {
                "parent_id": False,
                "date_start": date_start,
                "date_stop": date_stop,
                "seats": seats,
                "excess": excess,
                "allow_excess": allow_excess,
            }
        )

    def _create_enrolment(
        self,
        signup,
        training_action,
        register,
        deregister,
        state="joined",
        active=True,
    ):
        values = {
            "student_id": signup.student_id.id,
            "signup_id": signup.id,
            "training_action_id": training_action.id,
            "training_modality_id": self.training_modality.id,
            "full_enrolment": False,
            "register": register,
            "deregister": deregister,
            "active": active,
        }

        if state is not None:
            values["state"] = state

        return self.enrolment_obj.create(values)

    def _assert_validation_error(self, callback):
        with self.assertRaises(ValidationError):
            with self.env.cr.savepoint():
                callback()

    def _get_list_view_id(self, action):
        for view_id, view_mode in action.get("views", []):
            if view_mode == "list":
                return view_id

        self.fail("The window action does not contain a list view.")

    # -- Operational state ----------------------------------------------------

    def test_state_selection_and_default(self):
        state_field = self.enrolment_obj._fields["state"]
        selection = [value for value, _label in state_field.selection]

        self.assertEqual(
            selection,
            ["on_hold", "reserved", "joined"],
        )

        defaults = self.enrolment_obj.default_get(["state"])
        self.assertEqual(defaults["state"], "joined")

    def test_on_hold_remains_temporally_current(self):
        now = fields.Datetime.now()
        action = self._create_action(
            seats=1,
            excess=1,
            date_start=now - timedelta(days=1),
            date_stop=now + timedelta(days=1),
        )

        enrolment = self._create_enrolment(
            self.signup_1,
            action,
            now - timedelta(hours=1),
            now + timedelta(hours=1),
            state="on_hold",
        )

        self.assertTrue(enrolment.is_current)
        self.assertEqual(self.signup_1.student_id.current_enrolment_count, 1)

    def test_current_count_excludes_on_hold(self):
        now = fields.Datetime.now()
        action = self._create_action(
            seats=3,
            excess=3,
            date_start=now - timedelta(days=1),
            date_stop=now + timedelta(days=1),
        )

        register = now - timedelta(hours=1)
        deregister = now + timedelta(hours=1)

        self._create_enrolment(
            self.signup_1,
            action,
            register,
            deregister,
            state="on_hold",
        )
        self._create_enrolment(
            self.signup_2,
            action,
            register,
            deregister,
            state="reserved",
        )
        self._create_enrolment(
            self.signup_3,
            action,
            register,
            deregister,
            state="joined",
        )

        self.assertEqual(action.rollup_enrolment_count, 3)
        self.assertEqual(action.current_enrolment_count, 2)

    # -- Temporal capacity ----------------------------------------------------

    def test_on_hold_does_not_consume_capacity(self):
        action = self._create_action(seats=1, excess=1)
        register = datetime(2026, 2, 1, 9, 0)
        deregister = datetime(2026, 3, 1, 18, 0)

        self._create_enrolment(
            self.signup_1,
            action,
            register,
            deregister,
            state="on_hold",
        )
        joined = self._create_enrolment(
            self.signup_2,
            action,
            register,
            deregister,
            state="joined",
        )

        self.assertTrue(joined)

    def test_joined_consumes_capacity(self):
        action = self._create_action(seats=1, excess=1)
        register = datetime(2026, 2, 1, 9, 0)
        deregister = datetime(2026, 3, 1, 18, 0)

        self._create_enrolment(
            self.signup_1,
            action,
            register,
            deregister,
            state="joined",
        )

        self._assert_validation_error(
            lambda: self._create_enrolment(
                self.signup_2,
                action,
                register,
                deregister,
                state="joined",
            )
        )

    def test_reserved_consumes_capacity(self):
        action = self._create_action(seats=1, excess=1)
        register = datetime(2026, 2, 1, 9, 0)
        deregister = datetime(2026, 3, 1, 18, 0)

        self._create_enrolment(
            self.signup_1,
            action,
            register,
            deregister,
            state="reserved",
        )

        self._assert_validation_error(
            lambda: self._create_enrolment(
                self.signup_2,
                action,
                register,
                deregister,
                state="joined",
            )
        )

    def test_archived_enrolment_does_not_consume_capacity(self):
        action = self._create_action(seats=1, excess=1)
        register = datetime(2026, 2, 1, 9, 0)
        deregister = datetime(2026, 3, 1, 18, 0)

        self._create_enrolment(
            self.signup_1,
            action,
            register,
            deregister,
            state="joined",
            active=False,
        )
        joined = self._create_enrolment(
            self.signup_2,
            action,
            register,
            deregister,
            state="joined",
        )

        self.assertTrue(joined)

    def test_state_change_revalidates_capacity(self):
        action = self._create_action(seats=1, excess=1)
        register = datetime(2026, 2, 1, 9, 0)
        deregister = datetime(2026, 3, 1, 18, 0)

        joined = self._create_enrolment(
            self.signup_1,
            action,
            register,
            deregister,
            state="joined",
        )
        on_hold = self._create_enrolment(
            self.signup_2,
            action,
            register,
            deregister,
            state="on_hold",
        )

        self._assert_validation_error(
            lambda: on_hold.write({"state": "reserved"})
        )

        joined.write({"state": "on_hold"})
        on_hold.write({"state": "reserved"})

        self.assertEqual(on_hold.state, "reserved")

    def test_deregister_change_revalidates_capacity(self):
        action = self._create_action(seats=1, excess=1)

        first = self._create_enrolment(
            self.signup_1,
            action,
            datetime(2026, 2, 1, 9, 0),
            datetime(2026, 2, 10, 18, 0),
            state="joined",
        )
        second = self._create_enrolment(
            self.signup_2,
            action,
            datetime(2026, 2, 10, 18, 0),
            datetime(2026, 2, 20, 18, 0),
            state="joined",
        )

        self.assertTrue(second)

        self._assert_validation_error(
            lambda: first.write(
                {
                    "deregister": datetime(2026, 2, 15, 18, 0),
                }
            )
        )

    def test_register_change_revalidates_capacity(self):
        action = self._create_action(seats=1, excess=1)

        first = self._create_enrolment(
            self.signup_1,
            action,
            datetime(2026, 2, 1, 9, 0),
            datetime(2026, 2, 10, 18, 0),
            state="joined",
        )
        second = self._create_enrolment(
            self.signup_2,
            action,
            datetime(2026, 2, 10, 18, 0),
            datetime(2026, 2, 20, 18, 0),
            state="joined",
        )

        self.assertTrue(first)

        self._assert_validation_error(
            lambda: second.write(
                {
                    "register": datetime(2026, 2, 5, 9, 0),
                }
            )
        )

    def test_reactivation_revalidates_capacity(self):
        action = self._create_action(seats=1, excess=1)
        register = datetime(2026, 2, 1, 9, 0)
        deregister = datetime(2026, 3, 1, 18, 0)

        self._create_enrolment(
            self.signup_1,
            action,
            register,
            deregister,
            state="joined",
        )
        archived = self._create_enrolment(
            self.signup_2,
            action,
            register,
            deregister,
            state="joined",
            active=False,
        )

        self._assert_validation_error(
            lambda: archived.write({"active": True})
        )

    def test_touching_intervals_reuse_capacity(self):
        action = self._create_action(seats=1, excess=1)
        boundary = datetime(2026, 2, 10, 18, 0)

        first = self._create_enrolment(
            self.signup_1,
            action,
            datetime(2026, 2, 1, 9, 0),
            boundary,
            state="joined",
        )
        second = self._create_enrolment(
            self.signup_2,
            action,
            boundary,
            datetime(2026, 2, 20, 18, 0),
            state="joined",
        )

        self.assertTrue(first)
        self.assertTrue(second)

    def test_open_ended_enrolment_consumes_capacity(self):
        action = self._create_action(
            seats=1,
            excess=1,
            open_ended=True,
        )

        self._create_enrolment(
            self.signup_1,
            action,
            datetime(2026, 2, 1, 9, 0),
            False,
            state="joined",
        )

        self._assert_validation_error(
            lambda: self._create_enrolment(
                self.signup_2,
                action,
                datetime(2026, 3, 1, 9, 0),
                datetime(2026, 4, 1, 18, 0),
                state="joined",
            )
        )

    def test_zero_duration_enrolment_does_not_consume_capacity(self):
        action = self._create_action(seats=0, excess=0)
        moment = datetime(2026, 2, 1, 9, 0)

        enrolment = self._create_enrolment(
            self.signup_1,
            action,
            moment,
            moment,
            state="joined",
        )

        self.assertTrue(enrolment)

    # -- Excess capacity ------------------------------------------------------

    def test_excess_is_not_available_when_disabled(self):
        action = self._create_action(
            seats=1,
            excess=2,
            allow_excess=False,
        )
        register = datetime(2026, 2, 1, 9, 0)
        deregister = datetime(2026, 3, 1, 18, 0)

        self._create_enrolment(
            self.signup_1,
            action,
            register,
            deregister,
            state="joined",
        )

        self._assert_validation_error(
            lambda: self._create_enrolment(
                self.signup_2,
                action,
                register,
                deregister,
                state="joined",
            )
        )

    def test_excess_is_available_when_enabled(self):
        action = self._create_action(
            seats=1,
            excess=2,
            allow_excess=True,
        )
        register = datetime(2026, 2, 1, 9, 0)
        deregister = datetime(2026, 3, 1, 18, 0)

        first = self._create_enrolment(
            self.signup_1,
            action,
            register,
            deregister,
            state="joined",
        )
        second = self._create_enrolment(
            self.signup_2,
            action,
            register,
            deregister,
            state="joined",
        )

        self.assertTrue(first)
        self.assertTrue(second)

        self._assert_validation_error(
            lambda: self._create_enrolment(
                self.signup_3,
                action,
                register,
                deregister,
                state="joined",
            )
        )

    def test_disabling_excess_revalidates_existing_capacity(self):
        action = self._create_action(
            seats=1,
            excess=2,
            allow_excess=True,
        )
        register = datetime(2026, 2, 1, 9, 0)
        deregister = datetime(2026, 3, 1, 18, 0)

        self._create_enrolment(
            self.signup_1,
            action,
            register,
            deregister,
            state="joined",
        )
        self._create_enrolment(
            self.signup_2,
            action,
            register,
            deregister,
            state="joined",
        )

        self._assert_validation_error(
            lambda: action.write({"allow_excess": False})
        )

    def test_reducing_excess_revalidates_existing_capacity(self):
        action = self._create_action(
            seats=1,
            excess=3,
            allow_excess=True,
        )
        register = datetime(2026, 2, 1, 9, 0)
        deregister = datetime(2026, 3, 1, 18, 0)

        self._create_enrolment(
            self.signup_1,
            action,
            register,
            deregister,
            state="joined",
        )
        self._create_enrolment(
            self.signup_2,
            action,
            register,
            deregister,
            state="joined",
        )
        self._create_enrolment(
            self.signup_3,
            action,
            register,
            deregister,
            state="joined",
        )

        self._assert_validation_error(
            lambda: action.write({"excess": 2})
        )

    def test_reducing_seats_revalidates_when_excess_is_disabled(self):
        action = self._create_action(
            seats=2,
            excess=3,
            allow_excess=False,
        )
        register = datetime(2026, 2, 1, 9, 0)
        deregister = datetime(2026, 3, 1, 18, 0)

        self._create_enrolment(
            self.signup_1,
            action,
            register,
            deregister,
            state="joined",
        )
        self._create_enrolment(
            self.signup_2,
            action,
            register,
            deregister,
            state="joined",
        )

        self._assert_validation_error(
            lambda: action.write({"seats": 1})
        )

    def test_reducing_seats_is_allowed_when_excess_is_enabled(self):
        action = self._create_action(
            seats=3,
            excess=3,
            allow_excess=True,
        )
        register = datetime(2026, 2, 1, 9, 0)
        deregister = datetime(2026, 3, 1, 18, 0)

        self._create_enrolment(
            self.signup_1,
            action,
            register,
            deregister,
            state="joined",
        )
        self._create_enrolment(
            self.signup_2,
            action,
            register,
            deregister,
            state="joined",
        )
        self._create_enrolment(
            self.signup_3,
            action,
            register,
            deregister,
            state="joined",
        )

        action.write({"seats": 1})

        self.assertEqual(action.seats, 1)
        self.assertEqual(action._get_capacity_limit(), 3)

    def test_capacity_error_reports_effective_limit(self):
        action = self._create_action(
            seats=1,
            excess=2,
            allow_excess=True,
        ).with_context(lang="en_US")

        with self.assertRaises(ValidationError) as error:
            action._validate_enrolment_capacity(
                datetime(2026, 2, 1, 9, 0),
                3,
            )

        self.assertIn("capacity of 2 seats", str(error.exception))

    # -- Sign-up chronology ---------------------------------------------------

    def test_register_equal_to_signup_date_is_allowed(self):
        action = self._create_action(seats=2, excess=2)
        signup_date = datetime(2026, 2, 1, 9, 0)

        self.signup_1.write({"signup_date": signup_date})

        enrolment = self._create_enrolment(
            self.signup_1,
            action,
            signup_date,
            datetime(2026, 2, 10, 18, 0),
            state="joined",
        )

        self.assertTrue(enrolment)

    def test_register_cannot_precede_signup_date(self):
        action = self._create_action(seats=2, excess=2)
        self.signup_1.write(
            {"signup_date": datetime(2026, 2, 1, 9, 0)}
        )

        self._assert_validation_error(
            lambda: self._create_enrolment(
                self.signup_1,
                action,
                datetime(2026, 1, 31, 9, 0),
                datetime(2026, 2, 10, 18, 0),
                state="joined",
            )
        )

    def test_register_write_cannot_precede_signup_date(self):
        action = self._create_action(seats=2, excess=2)
        self.signup_1.write(
            {"signup_date": datetime(2026, 2, 1, 9, 0)}
        )

        enrolment = self._create_enrolment(
            self.signup_1,
            action,
            datetime(2026, 2, 10, 9, 0),
            datetime(2026, 2, 20, 18, 0),
            state="joined",
        )

        self._assert_validation_error(
            lambda: enrolment.write(
                {
                    "register": datetime(2026, 1, 15, 9, 0),
                }
            )
        )

    def test_signup_date_cannot_follow_first_register(self):
        action = self._create_action(seats=2, excess=2)

        self._create_enrolment(
            self.signup_1,
            action,
            datetime(2026, 2, 1, 9, 0),
            datetime(2026, 2, 10, 18, 0),
            state="joined",
        )

        self._assert_validation_error(
            lambda: self.signup_1.write(
                {
                    "signup_date": datetime(2026, 2, 2, 9, 0),
                }
            )
        )

        self.signup_1.write(
            {
                "signup_date": datetime(2026, 2, 1, 9, 0),
            }
        )

        self.assertEqual(
            self.signup_1.signup_date,
            datetime(2026, 2, 1, 9, 0),
        )

    def test_first_register_is_minimum_across_enrolments(self):
        action = self._create_action(seats=2, excess=2)

        self._create_enrolment(
            self.signup_1,
            action,
            datetime(2026, 2, 10, 9, 0),
            datetime(2026, 2, 12, 18, 0),
            state="joined",
        )
        self._create_enrolment(
            self.signup_1,
            action,
            datetime(2026, 2, 5, 9, 0),
            datetime(2026, 2, 7, 18, 0),
            state="joined",
        )

        first_by_signup = (
            self.signup_1._get_first_enrolment_register_by_signup()
        )

        self.assertEqual(
            first_by_signup[self.signup_1.id],
            datetime(2026, 2, 5, 9, 0),
        )

        self._assert_validation_error(
            lambda: self.signup_1.write(
                {
                    "signup_date": datetime(2026, 2, 6, 9, 0),
                }
            )
        )

    def test_archived_enrolment_participates_in_signup_chronology(self):
        action = self._create_action(seats=2, excess=2)

        self._create_enrolment(
            self.signup_1,
            action,
            datetime(2026, 2, 1, 9, 0),
            datetime(2026, 2, 10, 18, 0),
            state="joined",
            active=False,
        )

        self._assert_validation_error(
            lambda: self.signup_1.write(
                {
                    "signup_date": datetime(2026, 2, 2, 9, 0),
                }
            )
        )

    # -- Window actions and views --------------------------------------------

    def test_view_enrolments_uses_action_embed_list(self):
        action_record = self._create_action()
        action = action_record.view_enrolments()

        expected_view = self.env.ref(
            "academy_base."
            "view_academy_training_action_enrolment_embed_in_action"
        )

        self.assertEqual(
            self._get_list_view_id(action),
            expected_view.id,
        )
        self.assertEqual(
            action["context"]["default_training_action_id"],
            action_record.id,
        )
        self.assertEqual(
            action["context"]["default_parent_action_id"],
            action_record.id,
        )
        self.assertEqual(
            action["context"]["search_default_is_current"],
            1,
        )

    def test_view_rollup_enrolments_uses_action_embed_list(self):
        action_record = self._create_action()
        action = action_record.view_rollup_enrolments()

        expected_view = self.env.ref(
            "academy_base."
            "view_academy_training_action_enrolment_embed_in_action"
        )

        self.assertEqual(
            self._get_list_view_id(action),
            expected_view.id,
        )

    def test_view_training_action_groups_uses_group_embed_list(self):
        action_record = self._create_action()
        action = action_record.view_training_action_groups()

        expected_view = self.env.ref(
            "academy_base.view_academy_training_action_group_embed_tree"
        )

        self.assertEqual(
            self._get_list_view_id(action),
            expected_view.id,
        )

    def test_training_action_form_contains_capacity_option_once(self):
        view = self.env.ref("academy_base.view_academy_training_action_form")
        arch = etree.fromstring(view.arch_db.encode())

        allow_excess_nodes = arch.xpath(".//field[@name='allow_excess']")
        keep_synchronized_nodes = arch.xpath(
            ".//field[@name='keep_synchronized']"
        )

        self.assertEqual(len(allow_excess_nodes), 1)
        self.assertEqual(len(keep_synchronized_nodes), 1)

    def test_action_embed_view_hides_redundant_action_columns(self):
        view = self.env.ref(
            "academy_base."
            "view_academy_training_action_enrolment_embed_in_action"
        )
        arch = etree.fromstring(view.get_combined_arch().encode())

        for field_name in (
            "training_program_id",
            "parent_action_id",
            "manager_id",
        ):
            nodes = arch.xpath(f".//field[@name='{field_name}']")

            self.assertTrue(nodes)
            self.assertEqual(nodes[0].get("column_invisible"), "1")
