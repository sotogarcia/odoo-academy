# (bis|ter|quater|quinquies|sexies|septies|octies|novies|nonies|decies|undecies|duodecies|terdecies|quaterdecies|quindecies|sexdecies|septendecies|octodecies|novodecies|vicies|unvicies|duovicies|tervicies|quatervicies|quinvicies)?

SEARCH_BY_LAW_SQL = '''
    WITH source_data AS (
        SELECT
            atq."id",
            ( regexp_match ( att."name", '{law}', 'i' ) )[1]:: TEXT AS law,
            ( regexp_match ( atc."name", '{art}', 'i' ) )[2]:: INT AS article
        FROM
            academy_tests_question AS atq
            INNER JOIN academy_tests_topic AS att
                ON att."id" = atq.topic_id
            INNER JOIN academy_tests_question_category_rel AS rel
                ON rel.question_id = atq."id"
            INNER JOIN academy_tests_category AS atc
                ON atc."id" = rel.category_id
        WHERE
            TRUE {wand}
    ) SELECT DISTINCT
        "id"
    FROM source_data
    WHERE TRUE
'''
