# -*- coding: utf-8 -*-
""" Raw SQL sentences will be used in inverse search methods
"""


# INVERSE SEARCH: academy_tests.field_academy_tests_attempt__closed
# Raw sentence used to search attempts with no stored blank answers
# -----------------------------------------------------------------------------

TRAINING_ACTION_COUNT_SEARCH = '''
    WITH training_action_quantity AS (

            SELECT
                    training_activity_id,
                    COUNT ( * ) :: INTEGER AS quantity
            FROM
                    academy_training_action AS rel
            GROUP BY
                    training_activity_id

    )
    SELECT
            ata."id" AS training_activity_id
    FROM
            academy_training_activity AS ata
    LEFT JOIN training_action_quantity AS tac
            ON ata."id" = tac.training_activity_id
    WHERE
            COALESCE ( quantity, 0 ) :: INTEGER {} {}
'''
