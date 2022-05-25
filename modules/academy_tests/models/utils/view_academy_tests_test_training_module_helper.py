# -*- coding: utf-8 -*-

ACADEMY_TESTS_TEST_TRAINING_MODULE_HELPER = '''
     WITH linked AS (
        SELECT
            tree.requested_module_id,
            tree.responded_module_id,
            link.topic_id,
            link_rel.category_id
        FROM academy_training_module_tree_readonly tree
        JOIN academy_tests_topic_training_module_link link
            ON tree.responded_module_id = link.training_module_id
        LEFT JOIN
        academy_tests_category_tests_topic_training_module_link_rel link_rel
            ON link_rel.tests_topic_training_module_link_id = link.id
    ), direct_categories AS (
        SELECT
            linked.requested_module_id,
            linked.topic_id,
            linked.category_id
        FROM linked
        WHERE linked.category_id IS NOT NULL
    ), no_direct_categories AS (
        SELECT
            linked.requested_module_id,
            linked.topic_id,
            atc.id AS category_id
        FROM linked
        JOIN academy_tests_category atc ON atc.topic_id = linked.topic_id
        WHERE linked.category_id IS NULL
    ), full_set AS (
        SELECT
            direct_categories.requested_module_id,
            direct_categories.topic_id,
            direct_categories.category_id
        FROM direct_categories
        UNION ALL
            SELECT
                no_direct_categories.requested_module_id,
                no_direct_categories.topic_id,
                no_direct_categories.category_id
            FROM no_direct_categories
    ), module_category_rel AS (
        SELECT
            full_set.requested_module_id AS training_module_id,
            full_set.category_id AS test_category_id,
            full_set.topic_id
        FROM full_set
    ),  main_module_test_category_rel AS (
        -- Select MAIN-module<->category relationship
        SELECT
            test_category_id,
            COALESCE (
                atm.training_module_id, atm."id"
            ) :: INTEGER AS training_module_id
        FROM
            module_category_rel AS rel
        INNER JOIN academy_training_module AS atm
            ON rel.training_module_id = "id"
    ), mapped as (
        -- Select all questions, categories and main-modules related with
        -- tests and actions
        -- Duplicates are possible for questions
        SELECT
            rel1.test_id,
            atq."id" as question_id,
            rel2.category_id,
            rel3.training_module_id
        FROM
            academy_tests_test_question_rel AS rel1
            INNER JOIN academy_tests_question AS atq
                ON atq."id" = rel1.question_id
            INNER JOIN academy_tests_question_category_rel as rel2
                ON rel2.question_id = atq."id"
            INNER JOIN main_module_test_category_rel AS rel3
                ON rel2.category_id = rel3.test_category_id
    ), count_questions as (
        -- Select number of questions by category
        -- This will be used later to choose category with the lowerest
        -- number of questions
        SELECT
            category_id,
            COUNT ( question_id )::INTEGER as quantity
        FROM
            mapped
        GROUP BY
            category_id
    ), order_by_number_of_questions AS (
        -- Sort records by number of questions in the category and assign
        -- a ROW_NUMBER to each one
        -- This will be used later to get only select only those which
        -- have ROW_NUMBER = 1
        SELECT
            mp.*,
            ROW_NUMBER() OVER(
                PARTITION BY mp.test_id, mp.question_id
            ) AS index
        FROM
            mapped AS mp
        INNER JOIN count_questions AS cq
                ON mp.category_id = cq.category_id
        ORDER BY cq.quantity ASC
    ), unique_category_by_question AS (
        -- Prevents duplicate questions using those that have
        -- ROW_NUMBER = 1
        -- (category with lowerest number of questions)
        SELECT
            test_id, training_module_id
        FROM
            order_by_number_of_questions
        WHERE
            INDEX = 1
    ) -- , final_ids_and_count_questions AS (
            -- Select all valid ids and count questions
    SELECT
        test_id,
        training_module_id,
        COUNT(*)::INTEGER AS questions
    FROM
        unique_category_by_question
    GROUP BY
        test_id,
        training_module_id
'''
