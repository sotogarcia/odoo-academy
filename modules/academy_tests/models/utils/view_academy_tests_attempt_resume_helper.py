# -*- coding: utf-8 -*-

ACADEMY_TESTS_ATTEMPT_RESUME_HELPER = '''
WITH academy_tests_attempt_sanitized_answer AS (

    {} -- Requires SUBQUERY_ACADEMY_TESTS_ATTEMPT_SANITIZED_ANSWER

), attempt_question_count AS (

    -- The number of questions in the test for which the attempt was made
    -- This query count test-question links instead of test attempt answers

    SELECT
        att."id",
        link.test_id,
        COUNT(link."id")::INTEGER AS question_count
    FROM academy_tests_attempt AS att
        INNER JOIN academy_tests_test_training_assignment AS tta
            ON tta."id" = att.assignment_id
    LEFT JOIN academy_tests_test_question_rel AS link
        ON link."test_id" = tta."test_id"
    GROUP BY att."id", link.test_id

), transform_in_one_or_zero AS (

    -- This query generates one record for each attempt answer to all the
    -- questions, assigning values 1 or 0 based on different conditions.
    -- These values will be used later, in SQL aggregate functions, to generate
    -- statistics.

    SELECT
        attempt_id,
        instant,
        ( user_action <> 'blank' ) :: INTEGER AS answered,
        ( user_action = 'blank' ) :: INTEGER AS blank,
        ( user_action = 'answer' ) :: INTEGER AS answer,
        ( user_action = 'doubt' ) :: INTEGER AS doubt,
        ( user_action <> 'blank' AND is_correct ) :: INTEGER AS "right",
        ( user_action <> 'blank' AND NOT is_correct ) :: INTEGER AS wrong
    FROM
        academy_tests_attempt_sanitized_answer AS asa
    WHERE
        "leading" = 1

), aggregate_answer_count AS (

    -- This query groups the "transform_in_one_or_zero" query records by test
    -- attempt, using several aggregate functions to get global attempt basic
    -- statistics
    -- NOTE: This does not generate records for test attempts that do not have
    -- any questions

    SELECT
        attempt_id,
        MAX(instant)::TIMESTAMP AS instant,
        SUM("answered")::INTEGER AS answered_count,
        SUM("blank")::INTEGER AS blank_count,
        SUM("right")::INTEGER AS right_count,
        SUM("wrong")::INTEGER AS wrong_count,
        SUM("answer")::INTEGER AS answer_count,
        SUM("doubt")::INTEGER AS doubt_count
    FROM transform_in_one_or_zero
    GROUP BY attempt_id

), extended_statistics AS (

    -- This expands the results obtained in the "aggregate_answer_count" query
    -- NOTE: This does not generate records for test attempts that do not have
    -- any questions

    SELECT
        -- Attempt information
        attempt_id,
        aqc.test_id,

        -- Count items in attempt
        question_count,
        answered_count,
        right_count,
        wrong_count,
        blank_count,

        -- Score by attempt
        (question_count * att."right")::FLOAT AS max_points,
        (right_count * att."right")::FLOAT AS right_points,
        (wrong_count * att."wrong")::FLOAT AS wrong_points,
        (blank_count * att."blank")::FLOAT AS blank_points,

        -- Percents
        (answered_count / question_count::FLOAT)::FLOAT AS answered_percent,
        (right_count / question_count::FLOAT)::FLOAT AS right_percent,
        (wrong_count / question_count::FLOAT)::FLOAT AS wrong_percent,
        (blank_count / question_count::FLOAT)::FLOAT AS blank_percent,

        -- Other statistics
        answer_count,
        doubt_count

    FROM
        aggregate_answer_count AS aac
    INNER JOIN academy_tests_attempt AS att
        ON att."id" = aac.attempt_id
    INNER JOIN attempt_question_count AS aqc
        ON aqc."id" = att."id"
    where active

), attempt_default_values_if_test_have_no_questions AS (

    -- This query populates the values for all attempts, including those whose
    -- related test has no questions.

    SELECT
        att.*,
        att."id" AS attempt_id,
        idata.test_id,

        COALESCE(question_count, 0)::INTEGER AS question_count,
        COALESCE(answered_count, 0)::INTEGER AS answered_count,
        COALESCE(right_count, 0)::INTEGER AS right_count,
        COALESCE(wrong_count, 0)::INTEGER AS wrong_count,
        COALESCE(blank_count, 0)::INTEGER AS blank_count,
        COALESCE(answer_count, 0)::INTEGER AS answer_count,
        COALESCE(doubt_count, 0)::INTEGER AS doubt_count,

        COALESCE(max_points, 0.0)::FLOAT AS max_points,
        COALESCE(right_points, 0.0)::FLOAT AS right_points,
        COALESCE(wrong_points, 0.0)::FLOAT AS wrong_points,
        COALESCE(blank_points, 0.0)::FLOAT AS blank_points,

        COALESCE(answered_percent, 0.0)::FLOAT AS answered_percent,
        COALESCE(right_percent, 0.0)::FLOAT AS right_percent,
        COALESCE(wrong_percent, 0.0)::FLOAT AS wrong_percent,
        COALESCE(blank_percent, 1.0)::FLOAT AS blank_percent,

        CASE WHEN NOT idata.attempt_id IS NULL
            THEN (right_points + wrong_points + blank_points)
            ELSE 0.0
        END::float AS final_points

    FROM extended_statistics AS idata
    RIGHT JOIN academy_tests_attempt AS att
        ON att."id" = attempt_id
)
SELECT
    *,
    (final_points >= (max_points / 2.0))::BOOLEAN as passed,

    CASE WHEN (final_points >= (max_points / 2.0))
        THEN 'pass'
        ELSE 'fail'
    END::TEXT AS grade,

    CASE WHEN max_points > 0
        THEN (right_points / max_points * 10.0)
        ELSE 0.0
    END::FLOAT  AS right_score,

    CASE WHEN max_points > 0
        THEN (wrong_points / max_points  * 10.0)
        ELSE 0.0
    END::FLOAT  AS wrong_score,

    CASE WHEN max_points > 0
        THEN (blank_points / max_points  * 10.0)
        ELSE 0.0
    END::FLOAT  AS blank_score,

    CASE WHEN max_points > 0
        THEN (final_points / max_points  * 10.0)
        ELSE 0.0
    END::FLOAT  AS final_score,

    CASE WHEN max_points > 0
        THEN GREATEST(1, TRUNC(final_points / max_points  * 10.0))
        ELSE 0
    END::INTEGER  AS rating,

    ROW_NUMBER() OVER(wnd)::INTEGER AS "rank"

FROM attempt_default_values_if_test_have_no_questions
WINDOW wnd AS (
    PARTITION BY assignment_id, student_id
    ORDER BY assignment_id, student_id, final_points DESC
)
'''
