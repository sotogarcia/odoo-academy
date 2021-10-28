# -*- coding: utf-8 -*-
""" Raw SQL sentences will be used in inverse search methods

MODEL: academy_tests.model_academy_tests_answers_table
This model will be used to build and display as report a test answers table
"""


ACADEMY_TESTS_ANSWERS_TABLE_MODEL = '''
    WITH ordered_answers AS (
        -- Ensure answers sequence
        SELECT
            academy_tests_answer."id",
            (
                ROW_NUMBER () OVER (
                    PARTITION BY academy_tests_answer.question_id
                    ORDER BY
                        academy_tests_answer.question_id ASC,
                        academy_tests_answer."sequence" ASC,
                        academy_tests_answer."id" ASC
                )
            ) :: INTEGER AS "sequence",
            academy_tests_answer.question_id,
            academy_tests_answer.is_correct
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
            ROW_NUMBER () OVER (
                PARTITION BY rel.test_id
                ORDER BY
                    rel.test_id DESC,
                    rel."sequence" ASC,
                    rel."id" ASC
            ) AS atq_index
        FROM
            academy_tests_test_question_rel AS rel
        WHERE
            active = TRUE
        ORDER BY
            rel.test_id DESC,
            rel."sequence" ASC,
            rel."id" ASC
    ) -- Main query
    SELECT
        ROW_NUMBER () OVER (
            ORDER BY
                oq.test_id DESC,
                oq.atq_index ASC,
                oa."sequence" ASC,
                oa."id" ASC
        ) :: INTEGER AS "id",
        oq.test_id :: INTEGER,
        oq.question_id :: INTEGER,
        oa."id" :: INTEGER AS academy_tests_answer_id,
        oq.atq_index :: INTEGER AS "sequence",
        SUBSTRING (
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            FROM
                oa."sequence" FOR 1
        ) :: VARCHAR AS "name",
        atq."description" :: TEXT
    FROM
        ordered_quesions AS oq
    LEFT JOIN (
        SELECT
            *
        FROM
            ordered_answers
        WHERE
            is_correct IS TRUE
    ) AS oa ON oq.question_id = oa.question_id
    LEFT JOIN academy_tests_question AS atq
        ON atq."id" = oq.question_id
    ORDER BY
        oq.test_id DESC,
        oq.atq_index ASC,
        oa."sequence" ASC,
        oa."id" ASC
'''
