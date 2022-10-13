# -*- coding: utf-8 -*-
""" Used in academy.abstract.training and academy.abstract.training.reference
"""

from odoo.tools.translate import _

MAPPING_NAME_FIELD = {
    'academy.training.action.enrolment': 'action_name',
    'academy.training.action': 'action_name',
    'academy.training.activity': 'name',
    'academy.competency.unit': 'competency_name',
    'academy.training.module': 'name'
}

MAPPING_WAY_DOWN = {
    'academy.training.action.enrolment': 'training_action_id',
    'academy.training.action': 'training_activity_id',
    'academy.training.activity': 'competency_unit_ids',
    'academy.competency.unit': 'training_module_id',
    'academy.training.module': 'tree_ids'
}


MAPPING_MODEL_TYPE = {
    'academy.training.action.enrolment': 'enrolment',
    'academy.training.action': 'action',
    'academy.training.activity': 'activity',
    'academy.competency.unit': 'competency',
    'academy.training.module': 'module'
}

MAPPING_MODEL_FIELD = {
    'academy.training.action.enrolment': 'enrolment_id',
    'academy.training.action': 'training_action_id',
    'academy.training.activity': 'training_activity_id',
    'academy.competency.unit': 'competency_unit_id',
    'academy.training.module': 'training_module_id'
}

MAPPING_TRAINING_TYPES = [
    ('action', 'Training action'),
    ('activity', 'Training activity'),
    ('competency', 'Competency unit'),
    ('module', 'Training module'),
    ('enrolment', 'Student enrolment')
]

MAPPING_TRAINING_REFERENCES = [
    ('academy.training.action', _('Action')),
    ('academy.training.activity', _('Activity')),
    ('academy.competency.unit', _('Competency unit')),
    ('academy.training.module', _('Module')),
    ('academy.training.action.enrolment', _('Enrolment'))
]
