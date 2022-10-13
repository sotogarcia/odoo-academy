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
# List resources in training module including those linked to training units
# -----------------------------------------------------------------------------
ACADEMY_TRAINING_MODULE_AVAILABLE_RESOURCE_REL = """
    SELECT DISTINCT
        tree.requested_module_id AS training_module_id,
        rel.training_resource_id
    FROM
        academy_training_module_tree_readonly AS tree
    INNER JOIN academy_training_module_training_resource_rel AS rel
        ON tree."responded_module_id" = rel.training_module_id
"""

# Raw SQL used in Many2manyThroughView
# List resources in training activity including those linked to modules
# -----------------------------------------------------------------------------
ACADEMY_TRAINING_ACTIVITY_AVAILABLE_RESOURCE_REL = """
    WITH inherited_resources AS (
        SELECT
            atv."id" AS training_activity_id,
            atr."id" AS training_resource_id
        FROM
            academy_training_activity AS atv
        INNER JOIN academy_competency_unit AS acu
            ON atv."id" = acu.training_activity_id
        INNER JOIN academy_training_module AS atm
            ON acu.training_module_id = atm."id"
        LEFT JOIN academy_training_module AS atu
            ON atm."id" = atu.training_module_id or atm."id" = atu."id"
        INNER JOIN academy_training_module_training_resource_rel AS rel
            ON COALESCE (atu."id", atm."id") = rel.training_module_id
        LEFT JOIN academy_training_resource AS atr
            ON rel.training_resource_id = atr."id"
    )
    SELECT
        training_activity_id,
        training_resource_id
    FROM
        academy_training_activity_training_resource_rel AS rel
    UNION ALL (
        SELECT
            training_activity_id,
            training_resource_id
        FROM
            inherited_resources
    )
"""

# Raw SQL used in Many2manyThroughView
# List the resources in action, its activity or modules
# -----------------------------------------------------------------------------
ACADEMY_TRAINING_ACTION_AVAILABLE_RESOURCE_REL = """
    WITH module_resources AS (
        SELECT
                atv."id" AS training_activity_id,
                atr."id" AS training_resource_id
        FROM
                academy_training_activity AS atv
        INNER JOIN academy_competency_unit AS acu
                ON atv."id" = acu.training_activity_id
        INNER JOIN academy_training_module AS atm
                ON acu.training_module_id = atm."id"
        LEFT JOIN academy_training_module AS atu
                ON atm."id" = atu.training_module_id or atm."id" = atu."id"
        INNER JOIN academy_training_module_training_resource_rel AS rel
                ON COALESCE (atu."id", atm."id") = rel.training_module_id
        LEFT JOIN academy_training_resource AS atr
                ON rel.training_resource_id = atr."id"
    ), activity_resources AS (
        SELECT
            training_activity_id,
            training_resource_id
        FROM
            academy_training_activity_training_resource_rel AS rel
        UNION ALL (
            SELECT
                training_activity_id,
                training_resource_id
            FROM
                module_resources
        )
    ), inherited_resources AS (
        SELECT
            atc."id" as training_action_id,
            ars.training_resource_id
        FROM
            activity_resources AS ars
        INNER JOIN academy_training_action atc
            ON ars.training_activity_id = atc.training_activity_id

    ) SELECT
        training_action_id,
        training_resource_id
    FROM
            academy_training_action_training_resource_rel AS rel
    UNION ALL (
        SELECT
            training_action_id,
            training_resource_id
        FROM
            inherited_resources
    )
"""

# Raw SQL used in Many2manyThroughView
# List the resources in the enrollment, its action, activity or modules
# -----------------------------------------------------------------------------
ACADEMY_TRAINING_ACTION_ENROLMENT_AVAILABLE_RESOURCE_REL = """
    WITH training_enrolments AS (

        SELECT DISTINCT
            rel.training_resource_id,
            tae."id" AS enrolment_id
        FROM
            academy_training_action_enrolment_training_resource_rel AS rel
        INNER JOIN academy_training_action_enrolment AS tae
            ON tae."id" = rel.enrolment_id

    ), training_actions AS (

        SELECT DISTINCT
            rel.training_resource_id,
            tae."id" AS enrolment_id
        FROM
            academy_training_action_training_resource_rel AS rel
        INNER JOIN academy_training_action AS ata
            ON ata."id" = rel."training_action_id"
        INNER JOIN academy_training_action_enrolment AS tae
            ON tae.training_action_id = ata."id"
        WHERE ata.active

    ), training_activities as (

        SELECT DISTINCT
            rel.training_resource_id,
            tae."id" AS enrolment_id
        FROM
            academy_training_activity_training_resource_rel AS rel
        INNER JOIN academy_training_activity AS atc
            ON atc."id" = rel.training_activity_id
        INNER JOIN academy_training_action AS ata
            ON ata.training_activity_id = atc."id"
        INNER JOIN academy_training_action_enrolment AS tae
            ON tae.training_action_id = ata."id"
        WHERE ata.active AND atc.active

    ), competency_units AS (

        SELECT DISTINCT
            rel.training_resource_id,
            tae."id" AS enrolment_id
        FROM
            academy_competency_unit_training_resource_rel AS rel
        INNER JOIN academy_competency_unit AS acu
            ON acu."id" = rel.competency_unit_id
        INNER JOIN academy_training_activity AS atc
            ON atc."id" = acu.training_activity_id
        INNER JOIN academy_training_action AS ata
            ON ata.training_activity_id = atc."id"
        INNER JOIN academy_training_action_enrolment AS tae
            ON tae.training_action_id = ata."id"
        WHERE ata.active AND atc.active AND acu.active

    ), training_modules AS (

        SELECT DISTINCT
            rel.training_resource_id,
            tae."id" AS enrolment_id
        FROM
            academy_training_module_training_resource_rel AS rel
        INNER JOIN academy_training_module_tree_readonly AS tree
            ON tree.requested_module_id = rel."training_module_id"
        INNER JOIN academy_training_module AS atm
            ON atm."id" = tree.responded_module_id
        INNER JOIN academy_competency_unit AS acu
            ON acu.training_module_id = atm."id"
        INNER JOIN academy_training_activity AS atc
            ON atc."id" = acu.training_activity_id
        INNER JOIN academy_training_action AS ata
            ON ata.training_activity_id = atc."id"
        INNER JOIN academy_training_action_enrolment AS tae
            ON tae.training_action_id = ata."id"
        WHERE ata.active AND atc.active AND acu.active AND atm.active

    )
    SELECT enrolment_id, training_resource_id
        FROM training_enrolments UNION ALL
    SELECT enrolment_id, training_resource_id
        FROM training_actions UNION ALL
    SELECT enrolment_id, training_resource_id
        FROM training_activities UNION ALL
    SELECT enrolment_id, training_resource_id
        FROM competency_units UNION ALL
    SELECT enrolment_id, training_resource_id
        FROM training_modules
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
