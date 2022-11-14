# -*- coding: utf-8 -*-
""" Raw SQL sentences to perform different operations
"""


# COMPUTE DEFAULT VALUE: used in several academy.tests.question methods
# This allows to search for the last most recently used value for a given
# Many2one field. The ``{field}`` variable must be filled with field name.
# The number of records that will be taken into account can be established
# using ``LIMIT`` in the subquery clausule.
# -----------------------------------------------------------------------------

FIND_MOST_USED_QUESTION_FIELD_VALUE_FOR_SQL = '''
    SELECT
        {field},
        COUNT (*) AS counted
    FROM (
        SELECT
        {field}
        FROM academy_tests_question as atq
        INNER JOIN academy_tests_topic AS atp
            ON atp."id" = atq.topic_id
        WHERE atq.owner_id = {owner}
            AND atq.active IS TRUE
            AND atp.active IS TRUE
        ORDER BY atq.write_date DESC
        LIMIT {num}
    ) as sub
    GROUP BY
        {field}
    ORDER BY
        counted DESC
        LIMIT 1
'''


# COMPUTE DEFAULT VALUE: used in default_category_ids method
# This allows to search for the last most recently used category
# The number of records that will be taken into account can be established
# using ``LIMIT`` in the subquery clausule.
# -----------------------------------------------------------------------------

FIND_MOST_USED_QUESTION_CATEGORY_VALUE_SQL = '''
    SELECT
        category_id,
        COUNT (*) AS counted
    FROM
        (
        SELECT
            category_id
        FROM
            academy_tests_topic AS atp
            INNER JOIN academy_tests_category AS atc
                ON atc.topic_id = atp."id"
            INNER JOIN academy_tests_question_category_rel AS rel
                ON rel.category_id = atc."id"
            INNER JOIN academy_tests_question AS atq
                ON atq."id" = rel.question_id
        WHERE
            atc.active = TRUE
            AND atq.active = TRUE
            AND atp.active = TRUE
            AND atq.owner_id = {owner}
            AND atp."id" = {topic}
        ORDER BY
            atq.write_date DESC
            LIMIT 3
        ) AS sub
    GROUP BY
        category_id
    ORDER BY
        counted DESC
        LIMIT 1
'''


# PERFORM CHANGES IN DATABASE
# This will be used to sort by random keeping grouped questions with the same
# attachment or attachments. It packes ids in an SQL array, sort recordset and
# unnest the arrays.
# -----------------------------------------------------------------------------

ACADEMY_TESTS_SHUFFLE = '''
    WITH target_tests AS (
        -- Set target tests using ID
        SELECT UNNEST ( ARRAY [{}] ) :: INTEGER AS test_id
    ),

    block_order AS (
        -- Computes sequence of the first block in test exercise
        SELECT
            block_id,
            ROW_NUMBER ( ) OVER (
                ORDER BY "sequence" ASC ) :: INTEGER AS "sequence"
        FROM (
            -- Computes sequence by test ID and subsequence by block
            SELECT
                block_id,
                ROW_NUMBER ( ) OVER (
                    PARTITION BY test_id ORDER BY test_id, "sequence"
                ) AS "sequence",
                ROW_NUMBER ( ) OVER (
                    PARTITION BY test_id, block_id
                    ORDER BY test_id, "sequence"
                ) :: INTEGER AS "subsequence"
            FROM
                academy_tests_test_question_rel
            WHERE
                block_id IS NOT NULL
            ) AS src
        WHERE
            "subsequence" = 1
    ),

    block_grouping AS (
        -- Computes new question link sequences grouping by test, and block
        SELECT
            "id" AS link_id,
            COALESCE ( bo."sequence", 0 ) :: INTEGER AS block_sequence
        FROM
            academy_tests_test_question_rel AS rel
        LEFT JOIN block_order AS bo
            ON bo.block_id = rel.block_id
        ORDER BY
            bo."sequence" ASC NULLS FIRST,
            rel."sequence"
    ),

    question_attachment_relationship AS (
        -- Internal relationship between questions and attachments with the
        -- latter grouped
        SELECT
            rel.test_id,
            rel."id" AS link_id,
            ARRAY_AGG ( ira_rel.attachment_id ) AS attachs
        FROM
            academy_tests_question AS atq
        INNER JOIN academy_tests_test_question_rel AS rel
            ON rel.question_id = atq."id"
        INNER JOIN academy_tests_question_ir_attachment_rel AS ira_rel
            ON ira_rel.question_id = atq."id"
        INNER JOIN target_tests AS tt
            ON tt.test_id = rel.test_id
        GROUP BY
            rel.test_id,
            rel."id"
        ),

    without_attachments AS (
        -- Obtain all the questions with their attachments,
        -- grouping the IDs of the latter and assigning them a random index
        SELECT
            rel.test_id,
            rel."id" AS link_id
        FROM
            academy_tests_question AS atq
        INNER JOIN academy_tests_test_question_rel AS rel
            ON rel.question_id = atq."id"
        LEFT JOIN academy_tests_question_ir_attachment_rel AS ira_rel
            ON ira_rel.question_id = atq."id"
        INNER JOIN target_tests AS tt
            ON tt.test_id = rel.test_id
        WHERE
            ira_rel.question_id IS NULL
        ),

    with_nested_attachments AS (
        -- Get all questions without attachments and assigning them a random
        -- index
        SELECT
            test_id,
            attachs,
            ARRAY_AGG ( link_id ) AS question_ids,
            RANDOM( ) AS "index"
        FROM
            question_attachment_relationship
        GROUP BY
            test_id,
            attachs
        ORDER BY
            random( )
        ),

    full_set_of_questions AS (
        -- Make union including the questions with and without attachments
        SELECT
            test_id,
            "unnest" ( question_ids ) AS link_id,
            "attachs" AS attachment_ids,
            "index"
        FROM
            with_nested_attachments UNION ALL
        SELECT
            test_id,
            link_id,
            NULL,
            random( ) AS "index"
        FROM
            without_attachments
        ),

    new_sequences AS (
        -- Assign new sequence numbers using previous generated random indexes
        SELECT
            test_id,
            soq.link_id,
            ROW_NUMBER ( ) OVER (
                PARTITION BY test_id
                ORDER BY test_id DESC, block_sequence ASC, "index" ASC
            ) AS "sequence",
            attachment_ids
        FROM
            full_set_of_questions AS soq
        INNER JOIN block_grouping AS bg ON soq.link_id = bg.link_id
    )

    UPDATE academy_tests_test_question_rel AS links
    SET "sequence" = nsq."sequence"
    FROM
        new_sequences AS nsq
    WHERE
        nsq.link_id = links."id"
'''

# PERFORM CHANGES IN DATABASE
# This will be used to keep questions from the same block together
# -----------------------------------------------------------------------------

ACADEMY_TESTS_ARRANGE_BLOCKS = '''
    WITH target_tests AS (
        -- Set target tests using ID
        SELECT UNNEST ( ARRAY [ {} ] ) :: INTEGER AS test_id
    ),

    block_order AS (
        -- Computes sequence of the first block in test exercise
        SELECT
            block_id,
            ROW_NUMBER ( ) OVER (
                ORDER BY "sequence" ASC ) :: INTEGER AS "sequence"
        FROM (
            -- Computes sequence by test ID and subsequence by block
            SELECT
                block_id,
                ROW_NUMBER ( ) OVER (
                    PARTITION BY test_id
                    ORDER BY test_id, "sequence" ) AS "sequence",
                ROW_NUMBER ( ) OVER (
                    PARTITION BY test_id, block_id
                    ORDER BY test_id, "sequence" ) :: INTEGER AS "subsequence"
            FROM
                academy_tests_test_question_rel
            WHERE
                block_id IS NOT NULL
            ) AS src
        WHERE
            "subsequence" = 1
    ),

    block_grouping AS (
        -- Computes new question link sequences grouping by test, and block
        SELECT
            "id" AS link_id,
            ROW_NUMBER ( ) OVER (
                PARTITION BY rel.test_id
                    ORDER BY bo."sequence" ASC NULLS FIRST, rel."sequence"
            ) :: INTEGER AS "sequence"
        FROM
            academy_tests_test_question_rel AS rel
        INNER JOIN target_tests AS tt
            ON rel."test_id" = tt.test_id
        LEFT JOIN block_order AS bo
            ON bo.block_id = rel.block_id
        )
    UPDATE academy_tests_test_question_rel AS rel
        SET "sequence" = ns."sequence"
    FROM
        block_grouping AS ns
    WHERE
        rel."id" = ns."link_id"
'''
