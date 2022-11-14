
    checksum_sql = '''
        WITH answer_text AS (
            -- Appends x to the correct answers and # to the incorrect
            -- Convert text to lowercase

            SELECT
                question_id,
                (
                    CASE WHEN is_correct THEN 'x' ELSE'#' END
                    ||
                    LOWER ( "name" )
                ) :: VARCHAR AS "name"
            FROM
                academy_tests_answer

        ), answers AS (
            -- Creates an array with sorted answers
            -- In this way, questions with the same answers are considered
            -- the same regardless of their order.

            SELECT
                question_id,
                ARRAY_AGG ("name" ORDER BY "name" ASC)::VARCHAR[] AS answers
            FROM answer_text
                GROUP BY
                        question_id

        ), attachments AS (
            -- Convert checksum to lowercase
            -- Creates an array with sorted answers.
            -- In this way, questions with the same attachments are considered
            -- the same regardless of their order.

            SELECT
                question_id,
                ARRAY_AGG (
                    lower(checksum) ORDER BY rel."question_id", checksum ASC
                ) :: VARCHAR [] AS achecksums
            FROM
                academy_tests_question_ir_attachment_rel AS rel
            INNER JOIN ir_attachment atach
                ON rel.attachment_id = atach."id"
            GROUP BY
                question_id

        ), value_list AS (
            -- Ensures NOT null values

            SELECT
                atq."id" AS question_id,
                lower(
                    COALESCE(NULLIF( "preamble", '' ), 'Empty')
                )::VARCHAR AS preamble,
                lower("name") AS "name",
                answers,
                COALESCE(
                    achecksums, ARRAY[]::VARCHAR[]
                )::VARCHAR[] AS attachments
            FROM
                academy_tests_question AS atq
            INNER JOIN answers AS ans
                    ON ans."question_id" = atq."id"
            LEFT JOIN attachments AS att
                    ON att."question_id" = atq."id"
        )
        -- Computes the checksum for each question and returns a list of
        -- version-checksum pairs.
        -- In addition, it also returns the state and status to allow the
        --- same questions to coexist if they are being edited.

        SELECT
            vl.question_id,
            rel.topic_version_id AS version_id,
            status,
            active,
            UPPER(MD5(
                vl.preamble || '; ' ||
                vl."name" || '; ' ||
                ARRAY_TO_STRING(answers::VARCHAR[], '; ')::VARCHAR || '; ' ||
                ARRAY_TO_STRING(attachments, '; ')::VARCHAR
            ))::VARCHAR AS checksum
        FROM value_list AS vl
        INNER JOIN academy_tests_question AS atq
            ON atq."id" = vl.question_id
        LEFT JOIN academy_tests_question_topic_version_rel AS rel
            ON rel.question_id = atq."id"
    '''
