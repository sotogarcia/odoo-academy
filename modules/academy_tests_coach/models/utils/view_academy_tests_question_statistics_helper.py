VIEW_ACADEMY_TESTS_QUESTION_STATISTICS_HELPER = '''
    WITH final_answers AS (
        -- academy_tests_attempt_final_answer_helper
        {final}


    ), available_assignments AS (

        -- academy_training_action_enrolment_available_assignment_rel
        {available}

    ), absolute_values AS (
    SELECT
        {groupby} AS {related},
        question_id,
        MIN ( instant ) :: TIMESTAMP first_time,
        MAX ( instant ) :: TIMESTAMP last_time,
        COUNT ( * ) :: INTEGER AS retries,
        SUM ( ( user_action = 'blank' ) :: INTEGER ) AS blank_count,
        SUM ( ( user_action = 'answer' ) :: INTEGER ) AS answer_count,
        SUM ( ( user_action = 'doubt' ) :: INTEGER ) AS doubt_count,
        SUM ( is_correct :: INTEGER ) AS right_count,
        SUM (
            ( user_action != 'blank' AND NOT is_correct ) :: INTEGER
        ) AS wrong_count
    FROM
        academy_training_action_enrolment AS tae
    INNER JOIN available_assignments AS aa
        ON aa.enrolment_id = tae."id"
    INNER JOIN academy_tests_test_training_assignment AS ass
        ON ass."id" = aa.related_id
    INNER JOIN academy_tests_attempt AS att
        ON att.assignment_id = ass."id" AND att.student_id = tae.student_id
    INNER JOIN final_answers AS fa
        ON fa.attempt_id = att."id"
    WHERE
        ass.active and att.active
    GROUP BY
        {groupby},
        question_id
    ) SELECT
        ROW_NUMBER() OVER()::INTEGER AS "id",
        1::INTEGER AS create_uid,
        1::INTEGER AS write_uid,
        last_time AS create_date,
        last_time AS write_date,
        {related},
        question_id,
        first_time,
        last_time,

        retries,

        blank_count,
        answer_count,
        doubt_count,
        right_count,
        wrong_count,

        (answer_count + doubt_count)::INTEGER AS answer_doubt_count,
        (wrong_count + blank_count)::INTEGER AS wrong_blank_count,
        (wrong_count + doubt_count)::INTEGER AS wrong_doubt_count,
        (wrong_count + blank_count + doubt_count)::INTEGER
            AS wrong_blank_doubt_count,

        (blank_count / retries::FLOAT)::FLOAT AS  blank_percent,
        (answer_count / retries::FLOAT)::FLOAT AS  answer_percent,
        (doubt_count / retries::FLOAT)::FLOAT AS  doubt_percent,
        (right_count / retries::FLOAT)::FLOAT AS  right_percent,
        (wrong_count / retries::FLOAT)::FLOAT AS wrong_percent,

        ((answer_count + doubt_count) / retries::FLOAT)::FLOAT
            AS answer_doubt_percent,
        ((wrong_count + blank_count) / retries::FLOAT)::FLOAT
            AS wrong_blank_percent,
        ((wrong_count + doubt_count) / retries::FLOAT)::FLOAT
            AS wrong_doubt_percent,
        ((wrong_count + blank_count + doubt_count) / retries::FLOAT)::FLOAT
            AS wrong_blank_doubt_percent

    FROM absolute_values
'''
