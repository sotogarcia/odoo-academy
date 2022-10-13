# -*- coding: utf-8 -*-
""" Users may not answer all questions in one attempt, this query generates
records with default values for all unanswered questions and combines them with
existing ones.

┌───────────────────┐
│ QUERY RESULT      │
├───────────────────┤
│ id                │   - Virtual ID. This should not be used in relationships.
│ create_uid        │   - attempt.answer or attempt ``create_uid``
│ create_date       │   - attempt.answer or attempt ``create_date``
│ write_uid         │   - attempt.answer or attempt ``write_uid``
│ write_date        │   - attempt.answer or attempt ``write_date``
│ active            │   - attempt.answer or question ``active``
│ attempt_id        │
│ attempt_answer_id │   - can be null when user does not click on any answer
│ question_link_id  │
│ answer_id         │   - can be null when user leaves question blank
│ instant           │   - attempt.answer `instant` or attempt ``create_date``
│ user_action       │
│ leading           │   - row sorted in reverse order by ``instant`` (1-∞)
│ is_correct        │
└───────────────────┘
"""


SUBQUERY_ACADEMY_TESTS_ATTEMPT_SANITIZED_ANSWER = '''
WITH attempt_answer_values_from_answered_questions AS (

    -- This query selects "academy_tests_attempt" fields in the same
    -- order as "attempt_answer_default_values_for_non_answered_questions"
    -- subquery. This allow to perform an SQL UNION using both records
    -- NOTE: This query excludes non-active attempt answers

    SELECT
        "id",
        active,
        attempt_id,
        question_link_id,
        answer_id,
        instant,
        user_action,
        create_uid,
        create_date,
        write_uid,
        write_date
    FROM academy_tests_attempt_answer
    WHERE active IS TRUE

), attempt_answer_default_values_for_non_answered_questions AS (

    -- This query generates records for the "academy_tests_attempt"
    -- table with default values to be used for questions that have
    -- not been answered by the user.
    -- NOTE 1: This query also generates records for those questions
    -- that have all the answers for the attempt as not active

    SELECT
        ataa."id",
        atq.active,
        att."id" AS attempt_id,
        link."id" AS question_link_id,
        NULL::INTEGER AS "answer_id",
        att.create_date AS instant,
        'blank'::TEXT AS user_action,
        att.create_uid,
        att.create_date,
        att.write_uid,
        att.write_date
    FROM
        academy_tests_test_question_rel AS link
    INNER JOIN academy_tests_question AS atq
        ON atq."id" = link.question_id
    INNER JOIN academy_tests_test_training_assignment AS tta
        ON tta."test_id" = link.test_id
    INNER JOIN academy_tests_attempt AS att
        ON tta."id" = att.assignment_id
    LEFT JOIN attempt_answer_values_from_answered_questions AS ataa
        ON ataa.attempt_id  = att."id" AND ataa.question_link_id = link."id"
    WHERE ataa."id" IS NULL AND atq.active IS TRUE

), attempt_answer_for_all_questions AS (

    -- This query performs an SQL UNION using existing records
    -- from "academy_tests_attempt_answer" table and the new
    -- generated records for questions have not been answered
    -- by users.

    ( SELECT * FROM attempt_answer_values_from_answered_questions )
    UNION ALL
    ( SELECT * FROM attempt_answer_default_values_for_non_answered_questions )

)

SELECT
    ROW_NUMBER ( ) OVER ( ) :: INTEGER AS "id",

    aaq.create_uid,
    aaq.create_date,
    aaq.write_uid,
    aaq.write_date,

    aaq.active,

    aaq.attempt_id,
    aaq."id" AS attempt_answer_id,
    aaq.question_link_id,
    aaq.answer_id,

    aaq.instant,
    aaq.user_action,

    ROW_NUMBER ( ) OVER ( wnd ) :: INTEGER AS "leading",
    (aaq.user_action <> 'blank' AND is_correct IS TRUE)::BOOLEAN AS is_correct

FROM attempt_answer_for_all_questions AS aaq
INNER JOIN academy_tests_test_question_rel AS link
    ON link."id" = question_link_id
LEFT JOIN academy_tests_answer AS ans
    ON ans."id" = aaq.answer_id
WINDOW wnd AS (
    PARTITION BY attempt_id, question_link_id
    ORDER BY attempt_id, link."sequence", question_link_id, instant DESC
)
'''
