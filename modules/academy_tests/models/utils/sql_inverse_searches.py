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
        INNER JOIN academy_tests_attempt_final_answer_helper AS rel
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

# INVERSE SEARCH: academy_tests.field_academy_tests_topic__question_count
# Raw sentence used to search topics by number of questions
# -----------------------------------------------------------------------------

TOPIC_QUESTION_COUNT_SEARCH = '''
    WITH topic_question_quantity AS (
        SELECT
            topic_id,
            COUNT ( * ) :: INTEGER AS quantity
        FROM
            academy_tests_question AS atq
        GROUP BY
            topic_id
    )
    SELECT
        att."id" AS topic_id
    FROM
        academy_tests_topic AS att
    LEFT JOIN topic_question_quantity AS cmp
        ON att."id" = cmp.topic_id
    WHERE
        COALESCE ( quantity, 0 ) :: INTEGER {} {}
'''


# INVERSE SEARCH: academy_tests.field_academy_tests_category__question_count
# Raw sentence used to search categories by number of questions
# -----------------------------------------------------------------------------

CATEGORY_QUESTION_COUNT_SEARCH = '''
    WITH category_question_quantity AS (

        SELECT
            category_id,
            COUNT ( * ) :: INTEGER AS quantity
        FROM
            academy_tests_question_category_rel AS rel
        GROUP BY
            category_id

    )
    SELECT
        atc."id" AS category_id
    FROM
        academy_tests_category AS atc
    LEFT JOIN category_question_quantity AS cmp
        ON atc."id" = cmp.category_id
    WHERE
        COALESCE ( quantity, 0 ) :: INTEGER {} {}
'''


# INVERSE SEARCH: academy_tests.field_academy_tests_category__question_count
# Raw sentence used to search categories by number of questions
# -----------------------------------------------------------------------------

VERSION_QUESTION_COUNT_SEARCH = '''
    WITH category_question_quantity AS (

        SELECT
            version_id,
            COUNT ( * ) :: INTEGER AS quantity
        FROM
            academy_tests_question_version_rel AS rel
        GROUP BY
            version_id

    )
    SELECT
        ttv."id" AS version_id
    FROM
        academy_tests_version AS ttv
    LEFT JOIN category_question_quantity AS cmp
        ON ttv."id" = cmp.version_id
    WHERE
        COALESCE ( quantity, 0 ) :: INTEGER {} {}
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


# INVERSE SEARCH: academy_tests.field_academy_tests_attempt__passed
# Raw sentence used to search passed attempts
# -----------------------------------------------------------------------------
REQUEST_ATTEMPT_PASSED_SEARCH = '''
    SELECT
        "id"
    FROM
        academy_tests_attempt_resume_helper
    WHERE
        (final_points >= ( max_points / 2.0 )) = {}
'''


# INVERSE SEARCH: academy_tests.field_academy_tests__attempt_count
# Raw sentence used to search tests by number of attempts
# -----------------------------------------------------------------------------
SEARCH_TEST_ATTEMPT_COUNT = '''
    SELECT
        test_id,
        COUNT(*)::INTEGER AS num
    FROM
        academy_tests_attempt
    GROUP BY
        test_id
    HAVING
        COUNT(*) {} {}
'''


# INVERSE SEARCH: academy_tests.field_academy_student__attempt_count
# Raw sentence used to search students by number of attempts
# -----------------------------------------------------------------------------
SEARCH_STUDENT_ATTEMPT_COUNT = '''
    SELECT
    student_id,
    COUNT( * ) :: INTEGER AS num
    FROM
        academy_tests_attempt
    GROUP BY
        student_id
    HAVING
        COUNT(*) {} {}
'''
