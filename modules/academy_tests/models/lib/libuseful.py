# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" SQL

This module contains the sql used in some custom views
"""


#: All the different topics related to the test questions
ACADEMY_TESTS_TEST_TOPIC_IDS_SQL = """
    SELECT DISTINCT
        att."id" AS test_id,
        atp."id" AS topic_id
    FROM
        academy_tests_test AS att
    INNER JOIN academy_tests_test_question_rel AS rel ON att."id" = rel.test_id
    INNER JOIN academy_tests_question AS atq ON atq."id" = rel.question_id
    INNER JOIN academy_tests_topic AS atp ON atq.topic_id = atp."id"
    ORDER BY
        att."id" ASC,
        atp."id" ASC
"""

#: Relationship between attemp and its last answers
ACADEMY_TESTS_ATTEMPT_ATTEMPT_ANSWER_REL = '''
------------------------------------------------------------------------
--
-- Return the last attempt answer by attempt and question-link with some
-- related information.
-- This view will be used:
--   - as middle relationship table to link attempts and final answers
--   - in reports and view to quick get information about final answers
--
------------------------------------------------------------------------
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
    COALESCE(aptly, 0.0)::NUMERIC AS wrongly
FROM academy_tests_attempt AS atp
INNER JOIN academy_tests_test_question_rel as rel
    ON atp."test_id" = rel.test_id
LEFT JOIN finals AS fns
    ON fns.question_link_id = rel."id" AND atp."id" = fns."attempt_id"
LEFT JOIN stats AS sts
    ON sts.question_link_id = rel."id" AND atp."id" = sts."attempt_id"
LEFT JOIN academy_tests_answer AS ans
    ON ans."id" = fns.answer_id
''';

# -- OBSOLETE
# '''
#     WITH sorted AS (
#         SELECT
#             ataa."id" AS attempt_answer_id,
#             ataa.attempt_id,
#             ataa.question_link_id,
#             rel.question_id,
#             rel.test_id,
#             ataa.instant,
#             ataa.   answer_id,
#             user_action,
#             rel."sequence",
#             ( ROW_NUMBER ( ) OVER w ) :: INTEGER AS rn
#         FROM
#             academy_tests_attempt_answer ataa
#         LEFT JOIN academy_tests_test_question_rel rel
#             ON rel."id" = ataa.question_link_id
#         WINDOW w AS (
#             PARTITION BY ataa.attempt_id, ataa.question_link_id
#             ORDER BY ataa.instant DESC
#         )
#     ) SELECT
#         sorted.attempt_id,
#         sorted.attempt_answer_id,
#         sorted.test_id,
#         sorted.question_link_id,
#         sorted.question_id,
#         sorted."sequence",
#         user_action,
#         answer_id,
#         sorted.instant,
#                 is_correct
#     FROM
#         sorted as sorted
#         INNER JOIN academy_tests_answer AS ans ON ans."id" = sorted.answer_id
#     WHERE
#         ( sorted.rn = 1 )
#     ORDER BY
#         sorted.SEQUENCE
# '''




INHERITED_TOPICS_REL = '''
    SELECT
        tree."requested_module_id" as training_module_id,
        link."topic_id" as test_topic_id
    FROM
        academy_training_module_tree_readonly AS tree
    INNER JOIN academy_tests_topic_training_module_link AS link
        ON tree."responded_module_id" = link."training_module_id"
'''

INHERITED_CATEGORIES_REL = '''
    WITH linked AS (
        SELECT
            tree."requested_module_id",
            tree."responded_module_id",
            link."topic_id",
            link_rel."category_id"
        FROM
            academy_training_module_tree_readonly AS tree
        INNER JOIN academy_tests_topic_training_module_link AS link
            ON tree."responded_module_id" = link."training_module_id"
        LEFT JOIN academy_tests_category_tests_topic_training_module_link_rel AS link_rel
            ON link_rel."tests_topic_training_module_link_id" = link."id"
    ), direct_categories AS (
        SELECT
            requested_module_id,
            topic_id,
            category_id
        FROM
            linked
        WHERE
            category_id IS NOT NULL
    ), no_direct_categories AS (
        SELECT
            requested_module_id,
            linked."topic_id",
            atc."id" AS category_id
        FROM
            linked
        INNER JOIN academy_tests_category AS atc
            ON atc."topic_id" = linked."topic_id"
        WHERE
            linked."category_id" IS NULL
    ), full_set as (
        SELECT
            *
        FROM
            direct_categories
        UNION ALL SELECT
            *
        FROM
            no_direct_categories
        ) SELECT
            requested_module_id AS training_module_id,
            category_id AS test_category_id,
            topic_id
    FROM full_set
'''



ACADEMY_MODULE_AVAILABLE_TESTS = '''
WITH linked_to_training_units AS (
    SELECT
        test_id,
        atm.training_module_id
    FROM
        academy_tests_test_training_module_rel AS rel
    INNER JOIN academy_training_module AS atm
        ON rel.training_module_id = atm."id"
    WHERE atm.training_module_id IS NOT NULL
), linked_to_training_modules AS (
    SELECT
        test_id,
        atm."id" as training_module_id
    FROM
        academy_tests_test_training_module_rel AS rel
    INNER JOIN academy_training_module AS atm
        ON rel.training_module_id = atm."id"
    WHERE atm.training_module_id IS NULL

)
SELECT * FROM linked_to_training_modules
UNION
SELECT * FROM linked_to_training_units
'''


ACADEMY_COMPETENCY_AVAILABLE_TESTS = '''
WITH linked_to_training_units AS (
    SELECT
        test_id,
        acu."id" AS competency_unit_id
    FROM
        academy_tests_test_training_module_rel AS rel
    INNER JOIN academy_training_module AS atm
        ON rel.training_module_id = atm."id"
    INNER JOIN academy_competency_unit AS acu
        ON acu.training_module_id = atm.training_module_id
    WHERE atm.training_module_id IS NOT NULL
), linked_to_training_modules AS (
    SELECT
        test_id,
        acu."id" AS competency_unit_id
    FROM
        academy_tests_test_training_module_rel AS rel
    INNER JOIN academy_training_module AS atm
        ON rel.training_module_id = atm."id"
    INNER JOIN academy_competency_unit AS acu
        ON acu.training_module_id = atm."id"
    WHERE atm.training_module_id IS NULL
)
SELECT test_id, competency_unit_id FROM linked_to_training_units
UNION
SELECT test_id, competency_unit_id FROM linked_to_training_modules
UNION
SELECT test_id, competency_unit_id FROM academy_tests_test_competency_unit_rel
'''


ACADEMY_ACTIVITY_AVAILABLE_TESTS = '''
WITH linked_to_training_units AS (
    SELECT
        test_id,
        acu."training_activity_id"
    FROM
        academy_tests_test_training_module_rel AS rel
    INNER JOIN academy_training_module AS atm
        ON rel.training_module_id = atm."id"
    INNER JOIN academy_competency_unit AS acu
        ON acu.training_module_id = atm.training_module_id
    WHERE atm.training_module_id IS NOT NULL
), linked_to_training_modules AS (
    SELECT
        test_id,
        acu."training_activity_id"
    FROM
        academy_tests_test_training_module_rel AS rel
    INNER JOIN academy_training_module AS atm
        ON rel.training_module_id = atm."id"
    INNER JOIN academy_competency_unit AS acu
        ON acu.training_module_id = atm."id"
    WHERE atm.training_module_id IS NULL
), linked_to_competency_units AS (
    SELECT
        test_id,
        training_activity_id
    FROM academy_tests_test_competency_unit_rel AS rel
    INNER JOIN academy_competency_unit AS acu
        ON acu."id" = rel.competency_unit_id
)
SELECT test_id, training_activity_id FROM linked_to_training_units
UNION
SELECT test_id, training_activity_id FROM linked_to_training_modules
UNION
SELECT test_id, training_activity_id FROM linked_to_competency_units
UNION
SELECT test_id, training_activity_id FROM academy_tests_test_training_activity_rel
''';


ACADEMY_ACTION_AVAILABLE_TESTS = '''
WITH linked_to_training_units AS (
    SELECT
        test_id,
        atc."id" as training_action_id
    FROM
        academy_tests_test_training_module_rel AS rel
    INNER JOIN academy_training_module AS atm
        ON rel.training_module_id = atm."id"
    INNER JOIN academy_competency_unit AS acu
        ON acu.training_module_id = atm.training_module_id
    INNER JOIN academy_training_action AS atc
        ON acu.training_activity_id = atc.training_activity_id
    WHERE atm.training_module_id IS NOT NULL
), linked_to_training_modules AS (
    SELECT
        test_id,
        atc."id" as training_action_id
    FROM
        academy_tests_test_training_module_rel AS rel
    INNER JOIN academy_training_module AS atm
        ON rel.training_module_id = atm."id"
    INNER JOIN academy_competency_unit AS acu
        ON acu.training_module_id = atm."id"
    INNER JOIN academy_training_action AS atc
        ON acu.training_activity_id = atc.training_activity_id
    WHERE atm.training_module_id IS NULL
), linked_to_competency_units AS (
    SELECT
        test_id,
        atc."id" as training_action_id
    FROM academy_tests_test_competency_unit_rel AS rel
    INNER JOIN academy_competency_unit AS acu
        ON acu."id" = rel.competency_unit_id
    INNER JOIN academy_training_action AS atc
        ON acu.training_activity_id = atc.training_activity_id
), linked_to_training_activities AS (
    SELECT
        test_id,
        atc."id" as training_action_id
    FROM academy_tests_test_training_activity_rel AS rel
    INNER JOIN academy_training_action AS atc
        ON rel.training_activity_id = atc.training_activity_id
)
SELECT test_id, training_action_id FROM linked_to_training_units
UNION
SELECT test_id, training_action_id FROM linked_to_training_modules
UNION
SELECT test_id, training_action_id FROM linked_to_competency_units
UNION
SELECT test_id, training_action_id FROM linked_to_training_activities
UNION
SELECT test_id, training_action_id FROM academy_tests_test_training_action_rel
''';


ACADEMY_ENROLMENT_AVAILABLE_TESTS = '''
WITH linked_to_training_units AS (
    SELECT
        test_id,
        rel2.action_enrolment_id AS enrolment_id
    FROM
        academy_tests_test_training_module_rel AS rel
    INNER JOIN academy_training_module AS atm
        ON rel.training_module_id = atm."id"
    INNER JOIN academy_action_enrolment_training_module_rel AS rel2
        ON rel2.training_module_id = atm.training_module_id
    WHERE atm.training_module_id IS NOT NULL
), linked_to_training_modules AS (
    SELECT
        test_id,
        rel2.action_enrolment_id AS enrolment_id
    FROM
        academy_tests_test_training_module_rel AS rel
    INNER JOIN academy_training_module AS atm
        ON rel.training_module_id = atm."id"
    INNER JOIN academy_action_enrolment_training_module_rel AS rel2
        ON rel2.training_module_id = atm."id"
    WHERE atm.training_module_id IS NULL
), linked_to_competency_units AS (
    SELECT
        test_id,
        rel2.action_enrolment_id AS enrolment_id
    FROM academy_tests_test_competency_unit_rel AS rel
    INNER JOIN academy_competency_unit AS acu
        ON acu."id" = rel.competency_unit_id
    INNER JOIN academy_action_enrolment_training_module_rel AS rel2
        ON rel2.training_module_id = acu.training_module_id
    INNER JOIN academy_training_action AS atc
        ON atc.training_activity_id = acu.training_activity_id
    INNER JOIN academy_training_action_enrolment AS tae
        ON tae.training_action_id = atc."id"
), linked_to_training_activities AS (
    SELECT
        test_id,
        tae."id" AS enrolment_id
    FROM academy_tests_test_training_activity_rel AS rel
    INNER JOIN academy_training_action AS atc
        ON rel.training_activity_id = atc.training_activity_id
    INNER JOIN academy_training_action_enrolment AS tae
        ON tae.training_action_id = atc."id"
), linked_to_training_actions AS (
    SELECT
        test_id,
        tae."id" AS enrolment_id
    FROM academy_tests_test_training_action_rel AS rel
    INNER JOIN academy_training_action_enrolment AS tae
        ON tae.training_action_id = rel."training_action_id"
)
SELECT test_id, enrolment_id FROM linked_to_training_units
UNION
SELECT test_id, enrolment_id FROM linked_to_training_modules
UNION
SELECT test_id, enrolment_id FROM linked_to_competency_units
UNION
SELECT test_id, enrolment_id FROM linked_to_training_activities
UNION
SELECT test_id, enrolment_id FROM linked_to_training_actions
UNION
SELECT test_id, enrolment_id FROM academy_tests_test_training_action_enrolment_rel
'''


ACADEMY_STUDENT_AVAILABLE_TESTS = '''
WITH linked_to_training_units AS (
    SELECT
        test_id,
        tae.student_id
    FROM
        academy_tests_test_training_module_rel AS rel
    INNER JOIN academy_training_module AS atm
        ON rel.training_module_id = atm."id"
    INNER JOIN academy_action_enrolment_training_module_rel AS rel2
        ON rel2.training_module_id = atm.training_module_id
    INNER JOIN academy_training_action_enrolment AS tae
        ON tae."id" = rel2.action_enrolment_id
    WHERE atm.training_module_id IS NOT NULL
), linked_to_training_modules AS (
    SELECT
        test_id,
        tae.student_id
    FROM
        academy_tests_test_training_module_rel AS rel
    INNER JOIN academy_training_module AS atm
        ON rel.training_module_id = atm."id"
    INNER JOIN academy_action_enrolment_training_module_rel AS rel2
        ON rel2.training_module_id = atm."id"
    INNER JOIN academy_training_action_enrolment AS tae
        ON tae."id" = rel2.action_enrolment_id
    WHERE atm.training_module_id IS NULL
), linked_to_competency_units AS (
    SELECT
        test_id,
        tae.student_id
    FROM academy_tests_test_competency_unit_rel AS rel
    INNER JOIN academy_competency_unit AS acu
        ON acu."id" = rel.competency_unit_id
    INNER JOIN academy_action_enrolment_training_module_rel AS rel2
        ON rel2.training_module_id = acu.training_module_id
    INNER JOIN academy_training_action AS atc
        ON atc.training_activity_id = acu.training_activity_id
    INNER JOIN academy_training_action_enrolment AS tae
        ON tae.training_action_id = atc."id"
), linked_to_training_activities AS (
    SELECT
        test_id,
        tae.student_id
    FROM academy_tests_test_training_activity_rel AS rel
    INNER JOIN academy_training_action AS atc
        ON rel.training_activity_id = atc.training_activity_id
    INNER JOIN academy_training_action_enrolment AS tae
        ON tae.training_action_id = atc."id"
), linked_to_training_actions AS (
    SELECT
        test_id,
        tae.student_id
    FROM academy_tests_test_training_action_rel AS rel
    INNER JOIN academy_training_action_enrolment AS tae
        ON tae.training_action_id = rel."training_action_id"
)
SELECT test_id, student_id FROM linked_to_training_units
UNION
SELECT test_id, student_id FROM linked_to_training_modules
UNION
SELECT test_id, student_id FROM linked_to_competency_units
UNION
SELECT test_id, student_id FROM linked_to_training_activities
UNION
SELECT test_id, student_id FROM linked_to_training_actions
UNION
SELECT test_id, student_id FROM academy_tests_test_training_action_enrolment_rel AS rel
INNER JOIN academy_training_action_enrolment AS tae
    ON tae."id" = rel."enrolment_id"
'''
