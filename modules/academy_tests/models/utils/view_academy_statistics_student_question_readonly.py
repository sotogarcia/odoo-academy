# -*- coding: utf-8 -*-
""" Raw SQL sentences will be used in inverse search methods

MODEL: academy_tests.model_academy_statistics_student_question_readonly
This model will be used to show a report with the statistics student/question

┌────────────────────────────┐
│ QUERY RESULT               │
├────────────────────────────┤
│ id                         │
│ student_id                 │
│ question_id                │
│ attempts                   │
│ answer                     │
│ answer_percent             │
│ doubt_percent              │
│ blank_percent              │
│ right_percent              │
│ wrong_percent              │
│ answer_doubt_percent       │
│ blank_doubt_percent        │
│ blank_wrong_percent        │
│ doubt_wrong_percent        │
│ blank_doubt_wrong_percent  │
└────────────────────────────┘
"""

ACADEMY_STATISTICS_STUDENT_QUESTION_READONLY_MODEL = '''
    WITH academy_tests_attempt_sanitized_answer AS(

        {} -- Requires SUBQUERY_ACADEMY_TESTS_ATTEMPT_SANITIZED_ANSWER

    ), absolute_data AS (
        SELECT
            student_id,
            link.question_id,

            COUNT(*)::INTEGER AS attempts,

            SUM((asa.user_action = 'answer')::INTEGER)::INTEGER AS answer,
            SUM((asa.user_action = 'doubt')::INTEGER)::INTEGER AS doubt,
            SUM((asa.user_action = 'blank')::INTEGER)::INTEGER AS blank,

            SUM((asa.is_correct)::INTEGER)::INTEGER AS "right",
            (
                COUNT(*) -
                SUM((asa.user_action = 'blank' OR asa.is_correct)::INTEGER)
            )::INTEGER AS wrong,

            SUM(
                (asa.user_action != 'blank')::INTEGER
            )::INTEGER AS answer_doubt,
            SUM(
                (asa.user_action != 'answer')::INTEGER
            )::INTEGER AS blank_doubt,
            SUM(
                (asa.user_action = 'blank' OR NOT is_correct)::INTEGER
            )::INTEGER AS blank_wrong,

            SUM(
                (asa.user_action = 'doubt' OR NOT is_correct)::INTEGER
            )::INTEGER doubt_wrong,
            SUM(
                (asa.user_action <> 'answer' OR NOT asa.is_correct)::INTEGER
            )::INTEGER AS blank_doubt_wrong
        FROM
            academy_tests_attempt_sanitized_answer AS asa
        INNER JOIN academy_tests_attempt AS attempt
            ON asa.attempt_id = attempt."id"
        LEFT JOIN academy_tests_attempt_answer AS answer
            ON asa.answer_id = answer."id"
        INNER JOIN academy_tests_test_question_rel AS link
            ON link."id" = asa.question_link_id
        WHERE
            "leading" = 1
        GROUP BY
            student_id,
            link.question_id
    ) SELECT
        ROW_NUMBER() OVER() AS "id",
        student_id::INTEGER AS student_id,
        question_id::INTEGER AS question_id,
        attempts::NUMERIC AS attempts,
        answer::NUMERIC AS answer,
        (answer::NUMERIC / attempts)::NUMERIC AS answer_percent,
        doubt,
        (doubt::NUMERIC / attempts)::NUMERIC AS doubt_percent,
        blank,
        (blank::NUMERIC / attempts)::NUMERIC AS blank_percent,
        "right",
        ("right"::NUMERIC / attempts)::NUMERIC AS right_percent,
        wrong,
        (wrong::NUMERIC / attempts)::NUMERIC AS wrong_percent,
        answer_doubt,
        (answer_doubt::NUMERIC / attempts)::NUMERIC AS answer_doubt_percent,
        blank_doubt,
        (blank_doubt::NUMERIC / attempts)::NUMERIC AS blank_doubt_percent,
        blank_wrong,
        (blank_wrong::NUMERIC / attempts)::NUMERIC AS blank_wrong_percent,
        doubt_wrong,
        (doubt_wrong::NUMERIC / attempts)::NUMERIC AS doubt_wrong_percent,
        blank_doubt_wrong,
        (blank_doubt_wrong::NUMERIC / attempts) AS blank_doubt_wrong_percent
    FROM absolute_data
    WHERE COALESCE(attempts, 0) > 0
'''
