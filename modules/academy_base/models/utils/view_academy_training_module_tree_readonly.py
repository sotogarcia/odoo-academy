# -*- coding: utf-8 -*-
""" Users may not answer all questions in one attempt, this query generates
records with default values for all unanswered questions and combines them with
existing ones.
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
