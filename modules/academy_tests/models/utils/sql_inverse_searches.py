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

# INVERSE SEARCH: academy_tests.field_academy_tests_question__uncategorized
# Raw sentence used to search uncategorized questions
# -----------------------------------------------------------------------------

UNCATEGORIZED_QUESTION_SEARCH = '''
    SELECT DISTINCT ON
        ( atq."id" ) atq."id" AS question_id
    FROM
        academy_tests_question AS atq
        LEFT JOIN academy_tests_topic AS atp
            ON atp."id" = atq.topic_id
        LEFT JOIN academy_tests_question_category_rel AS rel1
            ON rel1.question_id = atq."id"
        LEFT JOIN academy_tests_category AS atc
            ON atc."id" = rel1.category_id
        LEFT JOIN academy_tests_question_topic_version_rel AS rel2
            ON rel2.question_id = atq."id"
        LEFT JOIN academy_tests_topic_version AS attv
            ON rel2.topic_version_id = attv."id"
    WHERE
        atp."id" IS NULL
        OR atc."id" IS NULL
        OR attv."id" IS NULL
        OR atp."active" IS FALSE
        OR atc."active" IS FALSE
        OR attv."active" IS FALSE
        OR atp."provisional" IS TRUE
        OR atc."provisional" IS TRUE
        OR attv."provisional" IS TRUE
'''


# INVERSE SEARCH: academy_tests.field_academy_tests_question_request__supplied
# Raw sentence used to search question requests by number of supplied questions
# -----------------------------------------------------------------------------
REQUEST_SUPPLIED_COUNT_SEARCH = '''
    SELECT
        request_id,
        COUNT ( question_id )
    FROM
        academy_tests_question_request_question_rel
    GROUP BY
        request_id
    HAVING COUNT ( question_id ) {} {}
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
