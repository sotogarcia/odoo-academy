# -*- coding: utf-8 -*-
""" Raw SQL sentences will be used in inverse search methods

MODEL: academy_tests.model_academy_tests_attempt_final_answer_helper
Relationship between attempt and its last answers

Return the last attempt answer by attempt and question-link with some
related information.
This view will be used:
  - as middle relationship table to link attempts and final answers
  - in reports and view to quick get information about final answers
"""


ACADEMY_TESTS_ATTEMPT_FINAL_ANSWER_HELPER = '''
WITH academy_tests_attempt_sanitized_answer AS (

    {} -- Requires SUBQUERY_ACADEMY_TESTS_ATTEMPT_SANITIZED_ANSWER

), attempt_answer_one_or_zero_values_for_statistics AS (

    -- This query generates one record for attempt answer to all
    -- the questions, assigning values 1 or 0 based on different
    -- conditions. These values will be used later, in aggregate
    -- functions, to generate statistics.

    SELECT
        attempt_id,
        question_link_id,
        ("id" IS NOT NULL)::INTEGER AS answered,
        (user_action = 'doubt')::INTEGER AS doubt,
        (user_action = 'blank')::INTEGER AS blank,
        (user_action = 'answer')::INTEGER AS answer,
        (user_action <> 'blank' AND is_correct)::INTEGER AS "right",
        (user_action <> 'blank' AND not is_correct)::INTEGER AS "wrong"
    FROM
        academy_tests_attempt_sanitized_answer

), attempt_answer_statistics AS (

    SELECT
        attempt_id,
        question_link_id,

        SUM(answered)::INTEGER AS retries,
        SUM(doubt)::INTEGER AS doubt_count,
        SUM(blank)::INTEGER AS blank_count,
        SUM(answer)::INTEGER AS answer_count,
        SUM("right")::INTEGER AS right_count,
        SUM("wrong")::INTEGER AS wrong_count,

        CASE WHEN SUM(answered) = 0
            THEN 0.0
            ELSE (SUM("right") / SUM(answered)::FLOAT)
        END::FLOAT AS aptly,

        CASE WHEN SUM(answered) = 0
            THEN 1.0
            ELSE ((SUM("wrong") + SUM(blank)) / SUM(answered)::FLOAT)
        END::FLOAT AS wrongly

    FROM attempt_answer_one_or_zero_values_for_statistics
    GROUP BY attempt_id, question_link_id

)

SELECT
    ROW_NUMBER( ) OVER ( wnd )::INTEGER AS "id",
    asa.create_uid,
    asa.create_date,
    asa.write_uid,
    asa.write_date,

    asa.active,
    asa.attempt_id,
    attempt_answer_id,
    asa.question_link_id,
    asa.answer_id,

    asa.instant,
    asa.user_action,
    asa.is_correct,

    retries,

    answer_count,
    doubt_count,

    blank_count,
    right_count,
    wrong_count,

    aptly,
    wrongly,

    -- Kept for backwards compatibility
    link.test_id,
    link.question_id,
    link."sequence"

FROM
    academy_tests_attempt_sanitized_answer AS asa
    INNER JOIN academy_tests_test_question_rel AS link
        ON link."id" = asa.question_link_id
    INNER JOIN attempt_answer_statistics AS aas
        ON asa.attempt_id = aas.attempt_id
    AND asa.question_link_id = aas.question_link_id
WHERE
    "leading" = 1
WINDOW wnd AS (
    ORDER BY  asa.attempt_id, "sequence" ASC
)
'''
