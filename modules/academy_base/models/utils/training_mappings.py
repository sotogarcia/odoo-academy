# -*- coding: utf-8 -*-
""" Used in academy.abstract.training and academy.abstract.training.reference
"""

from odoo.tools.translate import _lt

MAPPING_NAME_FIELD = {
    "academy.training.action.enrolment": "name",
    "academy.training.action": "name",
    "academy.training.program": "name",
    "academy.competency.unit": "name",
    "academy.training.module": "name",
}

MAPPING_WAY_DOWN = {
    "academy.training.action.enrolment": "training_action_id",
    "academy.training.action": "training_program_id",
    "academy.training.program": "competency_unit_ids",
    "academy.competency.unit": "training_module_id",
    "academy.training.module": "tree_ids",
}


MAPPING_MODEL_TYPE = {
    "academy.training.action.enrolment": "enrolment",
    "academy.training.action": "action",
    "academy.training.program": "activity",
    "academy.competency.unit": "competency",
    "academy.training.module": "module",
}

MAPPING_MODEL_FIELD = {
    "academy.training.action.enrolment": "enrolment_id",
    "academy.training.action": "training_action_id",
    "academy.training.program": "training_program_id",
    "academy.competency.unit": "competency_unit_id",
    "academy.training.module": "training_module_id",
}

MAPPING_TRAINING_TYPES = [
    ("action", "Training action"),
    ("activity", "Training program"),
    ("competency", "Competence Standard"),
    ("module", "Training module"),
    ("enrolment", "Student enrolment"),
]

MAPPING_TRAINING_REFERENCES = [
    ("academy.training.action", "Action"),
    ("academy.training.program", "Activity"),
    ("academy.competency.unit", "Competence Standard"),
    ("academy.training.module", "Module"),
    ("academy.training.action.enrolment", "Enrolment"),
]
