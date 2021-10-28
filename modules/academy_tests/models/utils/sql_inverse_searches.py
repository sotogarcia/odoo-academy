# -*- coding: utf-8 -*-
""" Raw SQL sentences will be used in inverse search methods
"""


# INVERSE SEARCH: academy_tests.field_academy_tests_attempt__closed
# Raw sentence used to search attempts with no stored blank answers
# -----------------------------------------------------------------------------

ATTEMPTS_CLOSED_SEARCH = '''
    WITH no_stored_blank_answers AS (
        SELECT
            ata."id",
            COUNT(*) AS no_stored
        FROM academy_tests_attempt AS ata
        INNER JOIN academy_tests_attempt_attempt_answer_rel AS rel
            ON ata."id" = rel.attempt_id and rel.attempt_answer_id IS NULL
        GROUP BY ata."id"
    ) SELECT
        ata."id"
    FROM
        academy_tests_attempt AS ata
        LEFT JOIN no_stored_blank_answers AS nsb ON ata."id" = nsb."id"
    WHERE
        COALESCE(no_stored, 0) = 0
        AND elapsed IS NOT NULL
        AND "end" IS NOT NULL
'''


# INVERSE SEARCH: academy_tests.field_academy_tests_question__answer_count
# Raw sentence used to search questions by number of answers
# -----------------------------------------------------------------------------

ANSWER_COUNT_SEARCH = '''
    WITH question_answer_quantity AS (
        SELECT
            question_id,
            COUNT ( * ) :: INTEGER AS quantity
        FROM
            academy_tests_answer
        GROUP BY
            question_id
    ) SELECT
        atq."id" AS question_id
    FROM
        academy_tests_question AS atq
    LEFT JOIN question_answer_quantity AS rel
        ON rel.question_id = atq."id"
    WHERE COALESCE(quantity, 0)::INTEGER {} {}
'''


# INVERSE SEARCH: academy_tests.field_academy_tests_test__question_count
# Raw sentence used to search test by number of questions
# -----------------------------------------------------------------------------

QUESTION_COUNT_SEARCH = '''
    WITH test_question_quantity AS (
        SELECT
            test_id,
            COUNT ( * ) :: INTEGER AS quantity
        FROM
            academy_tests_test_question_rel
        GROUP BY
            test_id
    ) SELECT
        att."id" AS test_id
    FROM
        academy_tests_test AS att
    LEFT JOIN test_question_quantity AS rel
        ON rel.test_id = att."id"
    WHERE COALESCE(quantity, 0)::INTEGER {} {}
'''
