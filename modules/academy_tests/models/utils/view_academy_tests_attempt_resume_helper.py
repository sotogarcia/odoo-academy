# -*- coding: utf-8 -*-

ACADEMY_TESTS_ATTEMPT_RESUME_HELPER = '''
    WITH hits AS (
        SELECT ct.attempt_id,
            COALESCE(ct."right", 0) AS "right",
            COALESCE(ct.wrong, 0) AS wrong
        FROM crosstab('
            SELECT
                attempt_id::int,
                CASE
                    WHEN is_correct THEN ''right''
                    ELSE ''wrong''
                END::TEXT AS user_action,
                COUNT ( * )::int
            FROM
                academy_tests_attempt_final_answer_helper AS rel
            WHERE user_action <> ''blank''
            GROUP BY
                attempt_id,
                is_correct
            ORDER BY 1,2'::text, '
            SELECT
                col
            FROM ( VALUES
                ( ''right'' ),
                ( ''wrong'' )
            ) tbl ( col )'::text) ct(
                attempt_id integer, "right" integer, wrong integer)
    ), user_actions AS (
        SELECT ct.attempt_id,
            COALESCE(ct.answer, 0) AS answer,
            COALESCE(ct.doubt, 0) AS doubt
        FROM crosstab('
            SELECT
                attempt_id::int,
                user_action::text,
                COUNT ( * )::int
            FROM
                academy_tests_attempt_final_answer_helper AS rel
            WHERE user_action <> ''blank''
            GROUP BY
                attempt_id,
                user_action
            ORDER BY 1,2
        '::text, '
            SELECT
                    col
            FROM ( VALUES
                ( ''answer'' ),
                ( ''doubt'' )
            ) tbl ( col )'::text) ct(
                attempt_id integer, answer integer, doubt integer)
    ), question_count AS (
     SELECT academy_tests_test_question_rel.test_id,
            (count(*))::integer AS questions
         FROM academy_tests_test_question_rel
        GROUP BY academy_tests_test_question_rel.test_id
    )
    SELECT
        ata."id",   -- This is de attempt ID
        ata.create_uid,
        ata.create_date,
        ata.write_uid,
        ata.write_date,
        ata."id" as resume_id,
        COALESCE((hits."right" + hits.wrong), 0)::INTEGER AS answered,
        COALESCE(hits."right", 0)::INTEGER AS right,
        COALESCE(hits.wrong, 0)::INTEGER AS wrong,
        COALESCE(ua.answer, 0)::INTEGER AS answer,
        COALESCE(ua.doubt, 0)::INTEGER AS doubt,
        (
            COALESCE(qc.questions, 0) -
            COALESCE((ua.doubt + ua.answer), 0)
        )::INTEGER  AS blank,
        COALESCE(qc.questions, 0)::INTEGER AS questions,
        (
            COALESCE(ata."right", 0.0) *
            COALESCE(hits."right", 0)
        )::NUMERIC as right_points,
        (
            COALESCE(ata."wrong", 0.0) *
            COALESCE(hits."wrong", 0)
        )::NUMERIC as wrong_points,
        (
            COALESCE(ata."blank", 0.0) * (COALESCE(qc.questions, 0) -
            COALESCE((ua.doubt + ua.answer), 0))
        )::NUMERIC as blank_points,
        (
            (COALESCE(ata."right", 0.0) * COALESCE(hits."right", 0)) +
            (COALESCE(ata."wrong", 0.0) * COALESCE(hits."wrong", 0)) +
            (COALESCE(ata."blank", 0.0) *(COALESCE(qc.questions, 0) -
            COALESCE((ua.doubt + ua.answer), 0)))
        )::NUMERIC as final_points,
        (
            COALESCE(qc.questions, 0) * COALESCE(ata."right", 0.0)
        )::NUMERIC AS max_points
    FROM academy_tests_attempt AS ata
    LEFT JOIN hits
        ON hits.attempt_id = ata.id
    LEFT JOIN user_actions ua
        ON ua.attempt_id = hits.attempt_id
    LEFT JOIN question_count AS qc
        ON qc.test_id = ata.test_id
    ORDER BY "start" DESC
'''
