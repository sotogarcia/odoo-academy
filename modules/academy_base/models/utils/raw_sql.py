# -*- coding: utf-8 -*-
""" This module contains several raw SQL sentences will be used by this module
"""

# Raw SQL used in Many2manyThroughView
# Link training actions and modules through an activity and a competency unit
# -----------------------------------------------------------------------------
ACADEMY_TRAINING_MODULE_USED_IN_TRAINING_ACTION_REL = '''
    SELECT
        atm."id" AS training_module_id,
        ata."id" AS training_action_id
    FROM
        academy_training_module AS atm
    INNER JOIN academy_competency_unit AS acu
        ON acu.training_module_id = atm."id"
    INNER JOIN academy_training_activity AS atc
        ON atc."id" = acu.training_activity_id
    INNER JOIN academy_training_action AS ata
        ON ata.training_activity_id = atc."id"
'''

# Raw SQL used in Many2manyThroughView
# Link training activities and modules through a competency unit
# -----------------------------------------------------------------------------
ACADEMY_TRAINING_ACTIVITY_TRAINING_MODULE_REL = """
    SELECT
        atv."id" AS training_activity_id,
        atm."id" AS training_module_id
    FROM
        academy_training_activity AS atv
    INNER JOIN academy_competency_unit AS acu
        ON atv."id" = acu.training_activity_id
    INNER JOIN academy_training_module AS atm
        ON acu.training_module_id = atm."id"
"""

# Raw SQL used in Many2manyThroughView
# Link training activities and training units through a competency unit and
# a training module
# -----------------------------------------------------------------------------
ACADEMY_TRAINING_ACTIVITY_TRAINING_UNIT_REL = """
    SELECT
        atv."id" AS training_activity_id,
        COALESCE(atu."id", atm."id")::INTEGER AS training_unit_id
    FROM
        academy_training_activity AS atv
    INNER JOIN academy_competency_unit AS acu
        ON atv."id" = acu.training_activity_id
    INNER JOIN academy_training_module AS atm
        ON acu.training_module_id = atm."id"
    LEFT JOIN academy_training_module AS atu
        ON atm."id" = atu.training_module_id
"""

# Raw SQL used in Many2manyThroughView
# Middle relations between training actions and students
# -----------------------------------------------------------------------------
ACADEMY_TRAINING_ACTION_STUDENT_REL = '''
    SELECT
        training_action_id,
        student_id
    FROM
        academy_training_action_enrolment
'''
