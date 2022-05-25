# -*- coding: utf-8 -*-
""" Raw SQL sentences will be used in inverse search methods

MODEL: academy_tests.model_academy_statistics_student_question_readonly
This model will be used to show a report with the statistics student/question
"""


ACADEMY_STATISTICS_STUDENT_QUESTION_READONLY_MODEL = '''
    WITH absolute_data AS (
        SELECT
            student_id,
            rel.question_id,

            COUNT(*)::INTEGER AS attempts,

            SUM((rel.user_action = 'answer')::INTEGER)::INTEGER AS answer,
            SUM((rel.user_action = 'doubt')::INTEGER)::INTEGER AS doubt,
            SUM((rel.user_action = 'blank')::INTEGER)::INTEGER AS blank,

            SUM((rel.is_correct)::INTEGER)::INTEGER AS "right",
            (
                COUNT(*) -
                SUM((rel.user_action = 'blank' OR rel.is_correct)::INTEGER)
            )::INTEGER AS wrong,

            SUM(
                (rel.user_action != 'blank')::INTEGER
            )::INTEGER AS answer_doubt,
            SUM(
                (rel.user_action != 'answer')::INTEGER
            )::INTEGER AS blank_doubt,
            SUM(
                (rel.user_action = 'blank' OR NOT is_correct)::INTEGER
            )::INTEGER AS blank_wrong,

            SUM(
                (rel.user_action = 'doubt' OR NOT is_correct)::INTEGER
            )::INTEGER doubt_wrong,
            SUM(
                (rel.user_action <> 'answer' OR NOT rel.is_correct)::INTEGER
            )::INTEGER AS blank_doubt_wrong
        FROM
            academy_tests_attempt_final_answer_helper AS rel
        INNER JOIN academy_tests_attempt AS attempt
            ON rel.attempt_id = attempt."id"
        LEFT JOIN academy_tests_attempt_answer AS answer
            ON rel.answer_id = answer."id"
        GROUP BY
            student_id,
            rel.question_id
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
