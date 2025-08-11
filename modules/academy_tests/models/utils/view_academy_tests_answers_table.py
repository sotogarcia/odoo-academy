# -*- coding: utf-8 -*-
""" Raw SQL sentences will be used in inverse search methods

MODEL: academy_tests.model_academy_tests_answers_table
This model will be used to build and display as report a test answers table


┌───────────────────┐
│ _answers_table    │
├───────────────────┤
│ id                │   - Virtual ID. This should not be used in relationships
│ question_id       │
│ sequence          │   - partitioned by test and ordered by link.sequence
│ name              │
│ description       │
│ link_id           │
└───────────────────┘
"""


ACADEMY_TESTS_ANSWERS_TABLE_MODEL = '''
WITH ordered_answers AS (
    -- Ensure answers sequence
    SELECT
        academy_tests_answer."id",
        ROW_NUMBER ( ) OVER (
            PARTITION BY academy_tests_answer.question_id
            ORDER BY academy_tests_answer.question_id ASC,
                     academy_tests_answer."sequence" ASC,
                     academy_tests_answer."id" ASC
        ) :: INTEGER AS "sequence",
        academy_tests_answer.question_id,
        academy_tests_answer.is_correct,
        SUBSTRING (
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ' :: VARCHAR,
            ROW_NUMBER ( ) OVER (
                PARTITION BY academy_tests_answer.question_id
                ORDER BY academy_tests_answer.question_id ASC,
                academy_tests_answer."sequence" ASC,
                academy_tests_answer."id" ASC
            ) :: INTEGER, 1 ) :: VARCHAR AS "name"
    FROM
        academy_tests_answer
    WHERE
        active = TRUE
    ORDER BY
        academy_tests_answer.question_id ASC,
        academy_tests_answer."sequence" ASC,
        academy_tests_answer."id" ASC
),

ordered_quesions AS (
    -- Ensure questions sequence
    SELECT
        rel.test_id,
        rel.question_id,
        ROW_NUMBER ( ) OVER (
            PARTITION BY rel.test_id
            ORDER BY rel.test_id DESC, rel."sequence" ASC, rel."id" ASC
        ) AS atq_index
    FROM
        academy_tests_test_question_rel AS rel
    INNER JOIN academy_tests_question AS atq 
        ON atq."id" = rel.question_id AND atq.active
    ORDER BY
        rel.test_id DESC,
        rel."sequence" ASC,
        rel."id" ASC
),

main_query AS (
    -- Main query
    SELECT
        oq.test_id :: INTEGER,
        oq.question_id :: INTEGER,
        STRING_AGG( oa."name", ', ' ORDER BY oa."name" ASC ) :: VARCHAR "name",
        MIN ( atq_index ) :: INTEGER AS atq_index
    FROM
        ordered_quesions AS oq
    LEFT JOIN ( SELECT * FROM ordered_answers WHERE is_correct IS TRUE ) AS oa
        ON oq.question_id = oa.question_id
    GROUP BY
        oq.test_id,
        oq.question_id
)
SELECT
    ROW_NUMBER ( ) OVER (
        ORDER BY mq.test_id DESC, atq_index ASC
    ) :: INTEGER AS "id",
    mq.test_id,
    mq.question_id,
    ROW_NUMBER ( ) OVER (
        PARTITION BY mq.test_id
        ORDER BY mq.test_id DESC, atq_index ASC
    ) :: INTEGER AS "sequence",
    mq."name",
    description,
    rel."id" AS link_id
FROM
    main_query AS mq
INNER JOIN academy_tests_question AS atq
    ON atq."id" = mq."question_id"
INNER JOIN academy_tests_test_question_rel AS rel
    ON rel.test_id = mq.test_id AND rel.question_id = mq.question_id
'''
