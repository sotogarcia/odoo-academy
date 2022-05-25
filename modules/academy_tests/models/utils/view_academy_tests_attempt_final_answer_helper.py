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
WITH sorted AS (
    -- Returns ID and inverse ordinal for attempt answer, these will be
    -- used in the ``finals`` query to get the last attempt answer by
    -- attempt and question-link
    SELECT
        ataa."id" AS attempt_answer_id,
        ( ROW_NUMBER ( ) OVER w ) :: INTEGER AS rn
    FROM
        academy_tests_attempt_answer AS ataa
    WINDOW w AS (
        PARTITION BY ataa.attempt_id, ataa.question_link_id
        ORDER BY ataa.instant DESC
    )
), finals AS (
    -- Get the last attempt answer record by attempt and question-link
    SELECT
        ataa.*
    FROM
        academy_tests_attempt_answer AS ataa
    INNER JOIN sorted
        ON ataa."id" = attempt_answer_id
    WHERE
        rn = 1
), stats AS (
    -- Computes the number of retries, right answers ratio, and wrong
    -- answers ratio by attempt and question-link
    SELECT
        ataa.attempt_id,
        ataa.question_link_id,
        COUNT ( * )::INTEGER AS retries,
        (SUM ( COALESCE ( is_correct, FALSE ) :: INTEGER ) :: DECIMAL / COUNT ( * ))::DECIMAL AS aptly,
        (1 - SUM ( COALESCE ( is_correct, FALSE ) :: INTEGER ) :: DECIMAL / COUNT ( * ))::DECIMAL AS wrongly
    FROM
        academy_tests_attempt_answer AS ataa
        INNER JOIN academy_tests_answer AS ans ON ans."id" = ataa.answer_id
    GROUP BY
        ataa.attempt_id,
        ataa.question_link_id
)
SELECT
    atp."id" as attempt_id,
    fns."id" as attempt_answer_id,
    rel.test_id,
    rel."id" as question_link_id,
    rel.question_id,
    rel."sequence",
    COALESCE(user_action, 'blank')::VARCHAR as user_action,
    answer_id,
    COALESCE(fns.instant, atp.create_date) as instant,
    COALESCE ( is_correct, FALSE ) :: BOOLEAN AS is_correct,
    COALESCE(retries, 1)::INTEGER AS retries,
    COALESCE(aptly, 0.0)::NUMERIC AS aptly,
    COALESCE(wrongly, 0.0)::NUMERIC AS wrongly
FROM academy_tests_attempt AS atp
INNER JOIN academy_tests_test_question_rel as rel
    ON atp."test_id" = rel.test_id
LEFT JOIN finals AS fns
    ON fns.question_link_id = rel."id" AND atp."id" = fns."attempt_id"
LEFT JOIN stats AS sts
    ON sts.question_link_id = rel."id" AND atp."id" = sts."attempt_id"
LEFT JOIN academy_tests_answer AS ans
    ON ans."id" = fns.answer_id
'''
