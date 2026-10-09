from datetime import datetime

from odoo.tests.common import TransactionCase


# ruff: noqa: DTZ001
class TestStudentSignupStateTransition(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.signup = cls.env.ref("academy_base.academy_student_signup_demo_1")

        source_action = cls.env.ref(
            "academy_base.academy_training_action_demo_1_default"
        )

        cls.training_action = source_action.copy(
            {
                "date_start": datetime(2026, 1, 1, 8, 0),
                "date_stop": datetime(2026, 12, 31, 22, 0),
                "parent_id": False,
            }
        )

        cls.open_training_action = source_action.copy(
            {
                "date_start": datetime(2026, 1, 1, 8, 0),
                "date_stop": False,
                "parent_id": False,
            }
        )

        cls.training_action_2 = source_action.copy(
            {
                "date_start": datetime(2026, 1, 1, 8, 0),
                "date_stop": datetime(2026, 12, 31, 22, 0),
                "parent_id": False,
            }
        )

        cls.training_action_3 = source_action.copy(
            {
                "date_start": datetime(2026, 1, 1, 8, 0),
                "date_stop": datetime(2026, 12, 31, 22, 0),
                "parent_id": False,
            }
        )

        cls.training_modality = cls.env.ref(
            "academy_base.academy_training_modality_classroom"
        )

    def _create_enrolment(
        self,
        training_action,
        register,
        deregister,
        active=True,
    ):
        return self.env["academy.training.action.enrolment"].create(
            {
                "student_id": self.signup.student_id.id,
                "signup_id": self.signup.id,
                "training_action_id": training_action.id,
                "training_modality_id": self.training_modality.id,
                "register": register,
                "deregister": deregister,
                "active": active,
            }
        )

    def _get_transitions(self, enrolment_ids):
        return self.env["academy.student.signup.state.transition"].search(
            [
                ("signup_id", "=", self.signup.id),
                ("enrolment_id", "in", enrolment_ids),
            ],
            order="timestamp, id",
        )

    def test_create_finite_enrolment_creates_state_transitions(self):
        register = datetime(2026, 2, 1, 9, 0)
        deregister = datetime(2026, 3, 1, 18, 0)

        enrolment = self.env["academy.training.action.enrolment"].create(
            {
                "student_id": self.signup.student_id.id,
                "signup_id": self.signup.id,
                "training_action_id": self.training_action.id,
                "training_modality_id": self.training_modality.id,
                "register": register,
                "deregister": deregister,
            }
        )

        transitions = self.signup.transition_ids.filtered(
            lambda transition: transition.enrolment_id == enrolment
        )

        self.assertEqual(len(transitions), 2)

        enrolled_transition = transitions.filtered(
            lambda transition: transition.state == "enrolled"
        )
        signed_up_transition = transitions.filtered(
            lambda transition: transition.state == "signed_up"
        )

        self.assertEqual(len(enrolled_transition), 1)
        self.assertEqual(len(signed_up_transition), 1)

        self.assertEqual(enrolled_transition.timestamp, register)
        self.assertEqual(signed_up_transition.timestamp, deregister)

    def test_create_open_enrolment_creates_only_enrolled_transition(self):
        register = datetime(2026, 2, 1, 9, 0)

        enrolment = self.env["academy.training.action.enrolment"].create(
            {
                "student_id": self.signup.student_id.id,
                "signup_id": self.signup.id,
                "training_action_id": self.open_training_action.id,
                "training_modality_id": self.training_modality.id,
                "register": register,
                "deregister": False,
            }
        )

        transitions = self.signup.transition_ids.filtered(
            lambda transition: transition.enrolment_id == enrolment
        )

        self.assertEqual(len(transitions), 1)

        transition = transitions.ensure_one()

        self.assertEqual(transition.state, "enrolled")
        self.assertEqual(transition.timestamp, register)

    def test_two_separated_enrolments_create_two_components(self):
        enrolment_obj = self.env["academy.training.action.enrolment"]

        enrolment_1 = enrolment_obj.create(
            {
                "student_id": self.signup.student_id.id,
                "signup_id": self.signup.id,
                "training_action_id": self.training_action.id,
                "training_modality_id": self.training_modality.id,
                "register": datetime(2026, 2, 1, 9, 0),
                "deregister": datetime(2026, 2, 10, 18, 0),
            }
        )

        enrolment_2 = enrolment_obj.create(
            {
                "student_id": self.signup.student_id.id,
                "signup_id": self.signup.id,
                "training_action_id": self.training_action.id,
                "training_modality_id": self.training_modality.id,
                "register": datetime(2026, 3, 1, 9, 0),
                "deregister": datetime(2026, 3, 10, 18, 0),
            }
        )

        components = self.signup._split_enrolment_components(
            enrolment_1 | enrolment_2
        )

        self.assertEqual(len(components), 2)

        transitions = self.signup.transition_ids.filtered(
            lambda transition: transition.enrolment_id
            in (enrolment_1 | enrolment_2)
        ).sorted("timestamp")

        self.assertEqual(len(transitions), 4)

        self.assertEqual(
            transitions.mapped("state"),
            [
                "enrolled",
                "signed_up",
                "enrolled",
                "signed_up",
            ],
        )

    def test_overlapping_enrolments_create_one_component(self):
        enrolment_obj = self.env["academy.training.action.enrolment"]

        enrolment_1 = enrolment_obj.create(
            {
                "student_id": self.signup.student_id.id,
                "signup_id": self.signup.id,
                "training_action_id": self.training_action.id,
                "training_modality_id": self.training_modality.id,
                "register": datetime(2026, 2, 1, 9, 0),
                "deregister": datetime(2026, 2, 10, 18, 0),
            }
        )

        enrolment_2 = enrolment_obj.create(
            {
                "student_id": self.signup.student_id.id,
                "signup_id": self.signup.id,
                "training_action_id": self.training_action_2.id,
                "training_modality_id": self.training_modality.id,
                "register": datetime(2026, 2, 5, 9, 0),
                "deregister": datetime(2026, 2, 15, 18, 0),
            }
        )

        components = self.signup._split_enrolment_components(
            enrolment_1 | enrolment_2
        )

        self.assertEqual(len(components), 1)

        component_enrolments, start_enrolment, closing_enrolment = components[
            0
        ]

        self.assertEqual(component_enrolments, enrolment_1 | enrolment_2)
        self.assertEqual(start_enrolment, enrolment_1)
        self.assertEqual(closing_enrolment, enrolment_2)

        transitions = self.signup.transition_ids.filtered(
            lambda transition: transition.enrolment_id
            in (enrolment_1 | enrolment_2)
        ).sorted("timestamp")

        self.assertEqual(len(transitions), 2)

        self.assertEqual(transitions[0].state, "enrolled")
        self.assertEqual(transitions[0].enrolment_id, enrolment_1)

        self.assertEqual(transitions[1].state, "signed_up")
        self.assertEqual(transitions[1].enrolment_id, enrolment_2)

    def test_same_register_uses_lowest_id_as_component_start(self):
        enrolment_obj = self.env["academy.training.action.enrolment"]

        register = datetime(2026, 2, 1, 9, 0)

        enrolment_1 = enrolment_obj.create(
            {
                "student_id": self.signup.student_id.id,
                "signup_id": self.signup.id,
                "training_action_id": self.training_action.id,
                "training_modality_id": self.training_modality.id,
                "register": register,
                "deregister": datetime(2026, 2, 10, 18, 0),
            }
        )

        enrolment_2 = enrolment_obj.create(
            {
                "student_id": self.signup.student_id.id,
                "signup_id": self.signup.id,
                "training_action_id": self.training_action_2.id,
                "training_modality_id": self.training_modality.id,
                "register": register,
                "deregister": datetime(2026, 2, 15, 18, 0),
            }
        )

        self.assertLess(enrolment_1.id, enrolment_2.id)

        components = self.signup._split_enrolment_components(
            enrolment_1 | enrolment_2
        )

        self.assertEqual(len(components), 1)

        _, start_enrolment, closing_enrolment = components[0]

        self.assertEqual(start_enrolment, enrolment_1)
        self.assertEqual(closing_enrolment, enrolment_2)

        transitions = self.signup.transition_ids.filtered(
            lambda transition: transition.enrolment_id
            in (enrolment_1 | enrolment_2)
        )

        enrolled_transition = transitions.filtered(
            lambda transition: transition.state == "enrolled"
        )

        self.assertEqual(len(enrolled_transition), 1)
        self.assertEqual(
            enrolled_transition.enrolment_id,
            enrolment_1,
        )
        self.assertEqual(
            enrolled_transition.timestamp,
            register,
        )

    def test_same_deregister_uses_lowest_id_as_component_close(self):
        enrolment_obj = self.env["academy.training.action.enrolment"]

        deregister = datetime(2026, 2, 15, 18, 0)

        enrolment_1 = enrolment_obj.create(
            {
                "student_id": self.signup.student_id.id,
                "signup_id": self.signup.id,
                "training_action_id": self.training_action.id,
                "training_modality_id": self.training_modality.id,
                "register": datetime(2026, 2, 5, 9, 0),
                "deregister": deregister,
            }
        )

        enrolment_2 = enrolment_obj.create(
            {
                "student_id": self.signup.student_id.id,
                "signup_id": self.signup.id,
                "training_action_id": self.training_action_2.id,
                "training_modality_id": self.training_modality.id,
                "register": datetime(2026, 2, 1, 9, 0),
                "deregister": deregister,
            }
        )

        self.assertLess(enrolment_1.id, enrolment_2.id)

        components = self.signup._split_enrolment_components(
            enrolment_1 | enrolment_2
        )

        self.assertEqual(len(components), 1)

        _, start_enrolment, closing_enrolment = components[0]

        self.assertEqual(start_enrolment, enrolment_2)
        self.assertEqual(closing_enrolment, enrolment_1)

        transitions = self.signup.transition_ids.filtered(
            lambda transition: transition.enrolment_id
            in (enrolment_1 | enrolment_2)
        )

        signed_up_transition = transitions.filtered(
            lambda transition: transition.state == "signed_up"
        )

        self.assertEqual(len(signed_up_transition), 1)
        self.assertEqual(
            signed_up_transition.enrolment_id,
            enrolment_1,
        )
        self.assertEqual(
            signed_up_transition.timestamp,
            deregister,
        )

    def test_write_joins_two_components(self):
        enrolment_1 = self._create_enrolment(
            self.training_action,
            datetime(2026, 2, 1, 9, 0),
            datetime(2026, 2, 10, 18, 0),
        )
        enrolment_2 = self._create_enrolment(
            self.training_action_2,
            datetime(2026, 2, 20, 9, 0),
            datetime(2026, 2, 28, 18, 0),
        )

        enrolment_ids = (enrolment_1 | enrolment_2).ids

        transitions = self._get_transitions(enrolment_ids)
        self.assertEqual(
            transitions.mapped("state"),
            [
                "enrolled",
                "signed_up",
                "enrolled",
                "signed_up",
            ],
        )

        enrolment_1.write(
            {
                "deregister": datetime(2026, 2, 20, 9, 0),
            }
        )

        transitions = self._get_transitions(enrolment_ids)

        self.assertEqual(len(transitions), 2)
        self.assertEqual(transitions[0].state, "enrolled")
        self.assertEqual(transitions[0].enrolment_id, enrolment_1)
        self.assertEqual(transitions[1].state, "signed_up")
        self.assertEqual(transitions[1].enrolment_id, enrolment_2)

    def test_write_splits_component(self):
        enrolment_1 = self._create_enrolment(
            self.training_action,
            datetime(2026, 2, 1, 9, 0),
            datetime(2026, 2, 10, 18, 0),
        )
        enrolment_2 = self._create_enrolment(
            self.training_action_2,
            datetime(2026, 2, 5, 9, 0),
            datetime(2026, 2, 15, 18, 0),
        )

        enrolment_ids = (enrolment_1 | enrolment_2).ids

        transitions = self._get_transitions(enrolment_ids)
        self.assertEqual(len(transitions), 2)

        enrolment_1.write(
            {
                "deregister": datetime(2026, 2, 4, 18, 0),
            }
        )

        transitions = self._get_transitions(enrolment_ids)

        self.assertEqual(len(transitions), 4)
        self.assertEqual(
            transitions.mapped("state"),
            [
                "enrolled",
                "signed_up",
                "enrolled",
                "signed_up",
            ],
        )

        self.assertEqual(transitions[0].enrolment_id, enrolment_1)
        self.assertEqual(transitions[1].enrolment_id, enrolment_1)
        self.assertEqual(transitions[2].enrolment_id, enrolment_2)
        self.assertEqual(transitions[3].enrolment_id, enrolment_2)

    def test_archive_and_reactivate_enrolment_updates_component(self):
        enrolment_1 = self._create_enrolment(
            self.training_action,
            datetime(2026, 2, 1, 9, 0),
            datetime(2026, 2, 10, 18, 0),
        )
        enrolment_2 = self._create_enrolment(
            self.training_action_2,
            datetime(2026, 2, 5, 9, 0),
            datetime(2026, 2, 15, 18, 0),
        )

        enrolment_ids = (enrolment_1 | enrolment_2).ids

        transitions = self._get_transitions(enrolment_ids)

        self.assertEqual(len(transitions), 2)
        self.assertEqual(transitions[0].enrolment_id, enrolment_1)
        self.assertEqual(transitions[1].enrolment_id, enrolment_2)

        enrolment_2.write({"active": False})

        transitions = self._get_transitions(enrolment_ids)

        self.assertEqual(len(transitions), 2)
        self.assertEqual(transitions[0].enrolment_id, enrolment_1)
        self.assertEqual(transitions[1].enrolment_id, enrolment_1)
        self.assertEqual(
            transitions.mapped("state"),
            ["enrolled", "signed_up"],
        )

        enrolment_2.write({"active": True})

        transitions = self._get_transitions(enrolment_ids)

        self.assertEqual(len(transitions), 2)
        self.assertEqual(transitions[0].enrolment_id, enrolment_1)
        self.assertEqual(transitions[0].state, "enrolled")
        self.assertEqual(transitions[1].enrolment_id, enrolment_2)
        self.assertEqual(transitions[1].state, "signed_up")

    def test_unlink_enrolment_removes_only_its_component_transitions(self):
        enrolment_1 = self._create_enrolment(
            self.training_action,
            datetime(2026, 2, 1, 9, 0),
            datetime(2026, 2, 10, 18, 0),
        )
        enrolment_2 = self._create_enrolment(
            self.training_action_2,
            datetime(2026, 3, 1, 9, 0),
            datetime(2026, 3, 10, 18, 0),
        )

        enrolment_1_id = enrolment_1.id
        enrolment_2_id = enrolment_2.id

        self.assertEqual(
            len(self._get_transitions([enrolment_1_id, enrolment_2_id])),
            4,
        )

        enrolment_1.unlink()

        self.assertFalse(self._get_transitions([enrolment_1_id]))

        transitions = self._get_transitions([enrolment_2_id])

        self.assertEqual(len(transitions), 2)
        self.assertEqual(
            transitions.mapped("state"),
            ["enrolled", "signed_up"],
        )

    def test_unlink_bridge_enrolment_splits_component(self):
        enrolment_1 = self._create_enrolment(
            self.training_action,
            datetime(2026, 2, 1, 9, 0),
            datetime(2026, 2, 5, 18, 0),
        )
        bridge = self._create_enrolment(
            self.training_action_2,
            datetime(2026, 2, 4, 9, 0),
            datetime(2026, 2, 11, 18, 0),
        )
        enrolment_3 = self._create_enrolment(
            self.training_action_3,
            datetime(2026, 2, 10, 9, 0),
            datetime(2026, 2, 15, 18, 0),
        )

        enrolment_ids = (enrolment_1 | bridge | enrolment_3).ids

        transitions = self._get_transitions(enrolment_ids)

        self.assertEqual(len(transitions), 2)
        self.assertEqual(transitions[0].enrolment_id, enrolment_1)
        self.assertEqual(transitions[1].enrolment_id, enrolment_3)

        bridge_id = bridge.id
        bridge.unlink()

        transitions = self._get_transitions([enrolment_1.id, enrolment_3.id])

        self.assertFalse(self._get_transitions([bridge_id]))

        self.assertEqual(len(transitions), 4)
        self.assertEqual(
            transitions.mapped("state"),
            [
                "enrolled",
                "signed_up",
                "enrolled",
                "signed_up",
            ],
        )

        self.assertEqual(transitions[0].enrolment_id, enrolment_1)
        self.assertEqual(transitions[1].enrolment_id, enrolment_1)
        self.assertEqual(transitions[2].enrolment_id, enrolment_3)
        self.assertEqual(transitions[3].enrolment_id, enrolment_3)

    def test_write_interior_enrolment_preserves_edge_transitions(self):
        enrolment_1 = self._create_enrolment(
            self.training_action,
            datetime(2026, 2, 1, 9, 0),
            datetime(2026, 2, 10, 18, 0),
        )
        enrolment_2 = self._create_enrolment(
            self.training_action_2,
            datetime(2026, 2, 4, 9, 0),
            datetime(2026, 2, 8, 18, 0),
        )
        enrolment_3 = self._create_enrolment(
            self.training_action_3,
            datetime(2026, 2, 7, 9, 0),
            datetime(2026, 2, 15, 18, 0),
        )

        enrolment_ids = (enrolment_1 | enrolment_2 | enrolment_3).ids

        transitions_before = self._get_transitions(enrolment_ids)

        self.assertEqual(len(transitions_before), 2)
        self.assertEqual(
            transitions_before[0].enrolment_id,
            enrolment_1,
        )
        self.assertEqual(
            transitions_before[1].enrolment_id,
            enrolment_3,
        )

        transition_ids_before = transitions_before.ids

        enrolment_2.write(
            {
                "register": datetime(2026, 2, 5, 9, 0),
                "deregister": datetime(2026, 2, 9, 18, 0),
            }
        )

        transitions_after = self._get_transitions(enrolment_ids)

        self.assertEqual(
            transitions_after.ids,
            transition_ids_before,
        )

    def test_partial_and_full_synchronization_produce_same_transitions(self):
        enrolment_1 = self._create_enrolment(
            self.training_action,
            datetime(2026, 2, 1, 9, 0),
            datetime(2026, 2, 5, 18, 0),
        )
        bridge = self._create_enrolment(
            self.training_action_2,
            datetime(2026, 2, 4, 9, 0),
            datetime(2026, 2, 11, 18, 0),
        )
        enrolment_3 = self._create_enrolment(
            self.training_action_3,
            datetime(2026, 2, 10, 9, 0),
            datetime(2026, 2, 15, 18, 0),
        )

        bridge.unlink()

        transitions_after_partial = self.signup.transition_ids.sorted(
            key=lambda transition: (
                transition.timestamp,
                transition.id,
            )
        )

        partial_values = [
            (
                transition.id,
                transition.state,
                transition.enrolment_id.id,
                transition.timestamp,
            )
            for transition in transitions_after_partial
        ]

        self.signup.synchronize_state_transitions()

        transitions_after_full = self.signup.transition_ids.sorted(
            key=lambda transition: (
                transition.timestamp,
                transition.id,
            )
        )

        full_values = [
            (
                transition.id,
                transition.state,
                transition.enrolment_id.id,
                transition.timestamp,
            )
            for transition in transitions_after_full
        ]

        self.assertEqual(partial_values, full_values)

        transitions = self._get_transitions(
            [
                enrolment_1.id,
                enrolment_3.id,
            ]
        )

        self.assertEqual(len(transitions), 4)
        self.assertEqual(
            transitions.mapped("state"),
            [
                "enrolled",
                "signed_up",
                "enrolled",
                "signed_up",
            ],
        )
        self.assertEqual(transitions[0].enrolment_id, enrolment_1)
        self.assertEqual(transitions[1].enrolment_id, enrolment_1)
        self.assertEqual(transitions[2].enrolment_id, enrolment_3)
        self.assertEqual(transitions[3].enrolment_id, enrolment_3)
