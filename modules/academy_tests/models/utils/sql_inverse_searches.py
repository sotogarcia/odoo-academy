# -*- coding: utf-8 -*-
""" Raw SQL sentences will be used in inverse search methods
"""



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


# INVERSE SEARCH: academy_tests.field_academy_student__attempt_count
# Raw sentence used to search students by number of attempts
# -----------------------------------------------------------------------------
SEARCH_IS_UNCATEGORIZED = '''
    WITH topics AS (

        SELECT
            atq."id" AS question_id
        FROM
            academy_tests_question AS atq
        INNER JOIN academy_tests_topic AS att ON atq.topic_id = att."id"
        WHERE
            att.provisional IS TRUE

    ), categories AS (

        SELECT
            rel.question_id
        FROM
            academy_tests_question_category_rel AS rel
        INNER JOIN academy_tests_category AS cat
            ON rel.category_id = cat."id"
        WHERE
            cat.provisional IS TRUE

    ), versions AS (

        SELECT
            rel.question_id
        FROM
            academy_tests_question_version_rel AS rel
        INNER JOIN academy_tests_version AS ver
            ON rel.version_id = ver."id"
        WHERE
            ver.provisional IS TRUE

    )
    SELECT
        *
    FROM
        topics
    UNION SELECT
        *
    FROM
        categories
    UNION SELECT
        *
    FROM
        versions
'''
