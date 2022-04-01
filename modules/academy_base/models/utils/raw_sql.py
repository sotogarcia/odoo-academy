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
    FROM academy_training_activity AS atv
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
    WITH module_test AS (
        -- Tests in related modules
        SELECT DISTINCT
                    rel2.action_enrolment_id as enrolment_id,
            rel.training_resource_id
        FROM
            academy_training_module_tree_readonly AS tree
        INNER JOIN academy_training_module_training_resource_rel AS rel
            ON tree."responded_module_id" = rel.training_module_id
        INNER JOIN academy_action_enrolment_training_module_rel AS rel2
            ON tree.requested_module_id = rel2.training_module_id
    ), action_test AS (
        -- Tests in action
        SELECT
            tae."id" as enrolment_id,
            rel.training_resource_id
        FROM
            academy_training_action_training_resource_rel AS rel
        INNER JOIN academy_training_action_enrolment AS tae
            ON tae.training_action_id = rel.training_action_id
    ), activity_test AS (
        -- Tests in related activity
        SELECT
            tae."id" as enrolment_id,
            rel.training_resource_id
        FROM
            academy_training_activity_training_resource_rel AS rel
        INNER JOIN academy_training_action AS atc
            ON rel.training_activity_id = atc.training_activity_id
        INNER JOIN academy_training_action_enrolment AS tae
            ON tae.training_action_id = atc."id"

    ), all_tests AS (
        -- All tests, this list can contains duplicated ids
        SELECT
            enrolment_id,
            training_resource_id
        FROM
            action_test
        UNION ALL (
            SELECT
                enrolment_id,
                training_resource_id
            FROM
                activity_test
        )
        UNION ALL (
            SELECT
                enrolment_id,
                training_resource_id
            FROM
                module_test
        )
    ) SELECT DISTINCT
        enrolment_id,
        training_resource_id
    FROM
        all_tests
"""

# Raw sentence used to create new model based on SQL VIEW
# Complex SQL allows to quick search training module-training unit dependencies
# -----------------------------------------------------------------------------
ACADEMY_TRAINING_MODULE_TREE_READONLY = '''
    WITH own_id AS (
    -- Request modules by id and respond with the own id
    SELECT
        "create_uid",
        "create_date",
        "write_uid",
        "write_date",
        "id" AS requested_module_id,
        "id" AS responded_module_id,
        "training_module_id" AS parent_module_id
    FROM
        academy_training_module
    ),  parent_id AS (
        -- Request modules by own id and respond with the parent id
        SELECT
            "create_uid",
            "create_date",
            "write_uid",
            "write_date",
            "id" AS requested_module_id,
            "training_module_id" AS responded_module_id,
            null::INTEGER AS parent_module_id
        FROM
            academy_training_module
        WHERE
            training_module_id IS NOT NULL
    ), child_id AS (
        -- Request modules by parent id and respond with own id
        SELECT
            "create_uid",
            "create_date",
            "write_uid",
            "write_date",
            "training_module_id" AS requested_module_id,
            "id" AS responded_module_id,
            training_module_id AS parent_module_id
        FROM
            academy_training_module
        WHERE
            training_module_id IS NOT NULL
    ), full_set as (
        -- Merge all queries into a single recordset
        SELECT
        *
        FROM
            own_id
        UNION ALL SELECT
            *
        FROM
            parent_id
        UNION ALL SELECT
            *
        FROM
            child_id
    ) SELECT
        "create_uid",
        "create_date",
        "write_uid",
        "write_date",
        requested_module_id,
        responded_module_id,
        parent_module_id
    FROM
        full_set
    ORDER BY
        requested_module_id ASC,
        responded_module_id ASC
'''

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
