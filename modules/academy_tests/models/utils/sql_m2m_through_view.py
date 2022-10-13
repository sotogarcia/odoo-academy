# -*- coding: utf-8 -*-
""" Raw SQL sentences will be used in inverse search methods
"""

# Many2manyThroughView:
# - academy_tests.field_academy_tests_question__topic_module_link_ids
# - academy_tests.field_academy_tests_topic_training_module_link__question_ids
# Raw sentence used to create new model based on SQL VIEW
# Computes all question dependencies based on chosen topics and categories
# -----------------------------------------------------------------------------
ACADEMY_TESTS_TOPIC_TRAINING_MODULE_LINK_QUESTION_REL = '''
    WITH questions AS (

        -- List all questions with their topic, version and categories
        SELECT
            atq."id" AS question_id,
            atq.topic_id,
            vrel.topic_version_id AS version_id,
            crel.category_id
        FROM
            academy_tests_question AS atq
        INNER JOIN academy_tests_question_category_rel AS crel
            ON crel.question_id = atq."id"
        INNER JOIN academy_tests_question_topic_version_rel AS vrel
            ON vrel.question_id = atq."id"

    ), topic_module_links AS (

        -- List all links with their topic, version and categories
        SELECT
            link."id" AS topic_module_link_id,
            topic_id,
            topic_version_id AS version_id,
            rel.category_id
        FROM academy_tests_topic_training_module_link AS link
        JOIN academy_tests_category_tests_topic_training_module_link_rel AS rel
            ON rel.tests_topic_training_module_link_id = link."id"

    )

    -- INNER JOIN when matching topic, version and categories
    SELECT DISTINCT
        topic_module_link_id,
        question_id
    FROM
        questions AS atq
    INNER JOIN topic_module_links AS tml
        ON tml.topic_id = atq.topic_id
        AND tml.version_id = atq.version_id
        AND tml.category_id = atq.category_id
'''


# Many2manyThroughView:
# - academy_tests.field_academy_tests_question__dependent_ids
# - academy_tests.field_academy_tests_test_question_rel__dependent_ids
# Raw sentence used to create new model based on SQL VIEW
# Complex recursive SQL allows to quick navigate in question dependecy tree
# -----------------------------------------------------------------------------
ACADEMY_TESTS_QUESTION_DEPENDENCY_REL = '''
    WITH RECURSIVE questions AS (
        SELECT
            "id",
            depends_on_id,
            ARRAY[]::INT[] AS depends_on_ids,
            1::INT AS "sequence",
            ARRAY[1]::INT[] AS "sequences"
        FROM academy_tests_question
        WHERE "depends_on_id" IS NULL

        UNION ALL

        SELECT
            atq."id",
            atq."depends_on_id",
            array_append(
                depends_on_ids, atq."depends_on_id") AS depends_on_ids,
            "sequence"+1 AS "sequence",
            array_append(sequences, "sequence" + 1)
        FROM  academy_tests_question AS atq
        INNER JOIN questions
            ON atq."depends_on_id" = questions."id"
    ),

    unpacked AS (
        SELECT
            "id" AS question_id,
            unnest(depends_on_ids) AS depends_on_id,
                    unnest(sequences) AS "sequence"
        FROM questions
    )
    SELECT DISTINCT
        unpacked.question_id,
        unpacked.depends_on_id
    FROM
        unpacked
    INNER JOIN academy_tests_question AS atq
        ON atq."id" = question_id
    WHERE
        unpacked."depends_on_id" IS NOT NULL
'''


# Many2manyThroughView:
# - academy_tests.field_academy_tests_test__topic_ids
# Relationship between topics and tests, througth the test questions
# -----------------------------------------------------------------------------
ACADEMY_TESTS_TEST_TOPIC_IDS_SQL = """
    SELECT DISTINCT
        att."id" AS test_id,
        atp."id" AS topic_id
    FROM
        academy_tests_test AS att
    INNER JOIN academy_tests_test_question_rel AS rel
        ON att."id" = rel.test_id
    INNER JOIN academy_tests_question AS atq
        ON atq."id" = rel.question_id
    INNER JOIN academy_tests_topic AS atp
        ON atq.topic_id = atp."id"
    ORDER BY
        att."id" ASC,
        atp."id" ASC
"""

# Many2manyThroughView:
# - academy_tests.field_academy_training_module__available_topic_ids
# Relationship between modules (units) and topics
# -----------------------------------------------------------------------------

INHERITED_TOPICS_REL = '''
    SELECT
        tree."requested_module_id" as training_module_id,
        link."topic_id" as test_topic_id
    FROM
        academy_training_module_tree_readonly AS tree
    INNER JOIN academy_tests_topic_training_module_link AS link
        ON tree."responded_module_id" = link."training_module_id"
'''


ACADEMY_COMPETENCY_UNIT_TEST_TOPIC_REL = '''
    SELECT DISTINCT
        acu."id" as competency_unit_id,
        link."topic_id" AS test_topic_id
    FROM
        academy_training_module_tree_readonly AS tree
    INNER JOIN academy_tests_topic_training_module_link AS link
        ON tree."responded_module_id" = link."training_module_id"
    INNER JOIN academy_competency_unit AS acu
        ON acu.training_module_id = link.training_module_id
'''

ACADEMY_TRAINING_ACTIVITY_TEST_TOPIC_REL = '''
    SELECT
        atc."id" as training_activity_id,
        link."topic_id" AS test_topic_id
    FROM
        academy_training_module_tree_readonly AS tree
    INNER JOIN academy_tests_topic_training_module_link AS link
        ON tree."responded_module_id" = link."training_module_id"
    INNER JOIN academy_competency_unit AS acu
        ON acu.training_module_id = link.training_module_id
    INNER JOIN academy_training_activity AS atc
        ON atc."id" = acu.training_activity_id
'''

# Many2manyThroughView:
# - academy_tests.field_academy_training_module__available_categories_ids
# Relationship between modules (units) and categories
# -----------------------------------------------------------------------------
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
        LEFT JOIN academy_tests_category_tests_topic_training_module_link_rel
            AS link_rel
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

ACADEMY_COMPETENCY_UNIT_TEST_CATEGORY_REL = '''
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
        LEFT JOIN academy_tests_category_tests_topic_training_module_link_rel
            AS link_rel
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
    ) SELECT DISTINCT
        acu."id" AS competency_unit_id,
        category_id AS test_category_id
    FROM
        full_set AS fs
    INNER JOIN academy_competency_unit AS acu
        ON fs.requested_module_id = acu.training_module_id
'''

ACADEMY_TRAINING_ACTIVITY_TEST_CATEGORY_REL = '''
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
        LEFT JOIN academy_tests_category_tests_topic_training_module_link_rel
            AS link_rel
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
    ) SELECT DISTINCT
        atc."id" AS training_activity_id,
        category_id AS test_category_id
    FROM
        full_set AS fs
    INNER JOIN academy_competency_unit AS acu
        ON fs.requested_module_id = acu.training_module_id
    INNER JOIN academy_training_activity AS atc
        ON atc."id" = acu.training_activity_id
'''




# Many2manyThroughView: Following SQL sentences will used to search available
# questions in a module. The following queries must be combined:
# · PARTIAL_ACADEMY_TESTS_QUESTION_TRAINING_MODULE
# · ACADEMY_TESTS_QUESTION_TRAINING_MODULE_REL
# · ACADEMY_TESTS_QUESTION_TRAINING_ACTIVITY_REL
# -----------------------------------------------------------------------------
PARTIAL_ACADEMY_TESTS_QUESTION_TRAINING_MODULE = '''
    WITH module_data AS (
        -- Topic, version and category by module (tree)
        SELECT
            requested_module_id AS training_module_id,
            link.topic_id,
            link.topic_version_id,
            rel.category_id
        FROM
            academy_tests_topic_training_module_link AS link
            INNER JOIN
            academy_tests_category_tests_topic_training_module_link_rel AS rel
                ON rel.tests_topic_training_module_link_id = link."id"
            INNER JOIN academy_training_module_tree_readonly AS tree
                ON responded_module_id = link.training_module_id
    ), question_data AS (
        -- Topic, version and category by question
        SELECT
            atq."id" AS question_id,
            atq.topic_id,
            rel1.topic_version_id,
            rel2.category_id
        FROM
            academy_tests_question AS atq
            INNER JOIN academy_tests_question_topic_version_rel AS rel1
                ON rel1.question_id = atq."id"
            INNER JOIN academy_tests_question_category_rel AS rel2
                ON atq."id" = rel2.question_id
    ), active_module_question_rel AS (
        -- Choose only matching active records
        SELECT
            training_module_id,
            question_id
        FROM
            module_data AS md
            -- Match module/question
            INNER JOIN question_data AS qd
                ON md.topic_id = qd.topic_id
                    AND md.topic_version_id = qd.topic_version_id
                    AND md.category_id = qd.category_id
            -- Limit to active records in middle relations
            INNER JOIN academy_tests_topic AS att
                ON att."id" = md.topic_id
                    AND att.active
            INNER JOIN academy_tests_topic_version AS ttv
                ON ttv."id" = md.topic_version_id
                    AND ttv.active
            INNER JOIN academy_tests_category AS atc
                ON atc."id" = md.category_id
                    AND atc.active
    )
'''

ACADEMY_TESTS_QUESTION_TRAINING_MODULE_REL = '''
    {}
    SELECT DISTINCT
        training_module_id,
        question_id
    FROM
        active_module_question_rel AS rel
'''

ACADEMY_TESTS_QUESTION_TRAINING_ACTIVITY_REL = '''
    {}
    SELECT DISTINCT
        training_activity_id,
        question_id
    FROM
        active_module_question_rel AS rel
    INNER JOIN academy_competency_unit AS acu
        ON acu.training_module_id = rel.training_module_id
    INNER JOIN academy_training_activity AS act
        ON act."id" = acu.training_activity_id
'''

ACADEMY_TESTS_QUESTION_DUPLICATED_REL = '''
    WITH duplicates AS (
        SELECT
            checksum,
            MIN ( atq."id" ) :: INTEGER AS original_id,
            ARRAY_AGG ( atq."id" ) :: INTEGER [] AS question_ids
        FROM
            academy_tests_question AS atq
        WHERE
            checksum IS NOT NULL
            AND status <> 'draft'
            AND active = True
        GROUP BY
            checksum
        HAVING
            COUNT ( atq."id" ) > 1
    ), unnested AS (
        SELECT
            original_id AS question_id,
            UNNEST ( question_ids ) AS duplicate_id
        FROM
            duplicates
    )
    SELECT
        question_id,
        duplicate_id
    FROM
        unnested AS unn
    WHERE
        question_id <> duplicate_id
    ORDER BY
        question_id ASC,
        duplicate_id DESC
'''

ACADEMY_TESTS_QUESTION_DUPLICATED_BY_OWNER_REL = '''
    WITH duplicates AS (
        SELECT
            checksum,
            MIN ( atq."id" ) :: INTEGER AS original_id,
            ARRAY_AGG ( atq."id" ) :: INTEGER [] AS question_ids
        FROM
            academy_tests_question AS atq
        WHERE
            checksum IS NOT NULL
            AND status <> 'draft'
            AND active = True
        GROUP BY
            checksum
        HAVING
            COUNT ( atq."id" ) > 1
    ), unnested AS (
        SELECT
            original_id AS question_id,
            UNNEST ( question_ids ) AS duplicate_id
        FROM
            duplicates
    )
    SELECT
        duplicate_id,
        "duplicate_atq"."owner_id" AS duplicate_owner_id
    FROM
        unnested AS unn
        INNER JOIN academy_tests_question AS duplicate_atq
            ON duplicate_atq."id" = duplicate_id
    WHERE
        question_id <> duplicate_id
    ORDER BY
        question_id ASC,
        duplicate_id DESC
'''


# Many2manyThroughView: Blocks by test
# -----------------------------------------------------------------------------

ACADEMY_TESTS_TEST_TEST_BLOCK_REL = '''
    SELECT DISTINCT
        test_id,
        test_block_id
    FROM
        academy_tests_test_question_rel
    WHERE
        test_block_id IS NOT NULL
'''

# Many2manyThroughView: ???
# -----------------------------------------------------------------------------

ACADEMY_TESTS_TEST_TRAINING_ASSIGNMENT_STUDENT_REL = '''
    WITH training_enrolments AS (

        SELECT DISTINCT
            tta."id" AS assignment_id,
            tta.training_ref,
            tae.student_id
        FROM
            academy_tests_test_training_assignment AS tta
        INNER JOIN academy_training_action_enrolment AS tae
            ON tae."id" = tta.enrolment_id

    ), training_actions AS (

        SELECT DISTINCT
            tta."id" AS assignment_id,
            tta.training_ref,
            tae.student_id
        FROM
            academy_tests_test_training_assignment AS tta
        INNER JOIN academy_training_action AS ata
            ON ata."id" = tta."training_action_id"
        INNER JOIN academy_training_action_enrolment AS tae
            ON tae.training_action_id = ata."id"
        WHERE ata.active

    ), training_activities as (

        SELECT DISTINCT
            tta."id" AS assignment_id,
            tta.training_ref,
            tae.student_id
        FROM
            academy_tests_test_training_assignment AS tta
        INNER JOIN academy_training_activity AS atc
            ON atc."id" = tta.training_activity_id
        INNER JOIN academy_training_action AS ata
            ON ata.training_activity_id = atc."id"
        INNER JOIN academy_training_action_enrolment AS tae
            ON tae.training_action_id = ata."id"
        WHERE ata.active AND atc.active

    ), competency_units AS (

        SELECT DISTINCT
            tta."id" AS assignment_id,
            tta.training_ref,
            tae.student_id
        FROM
            academy_tests_test_training_assignment AS tta
        INNER JOIN academy_competency_unit AS acu
            ON acu."id" = tta.competency_unit_id
        INNER JOIN academy_training_activity AS atc
            ON atc."id" = acu.training_activity_id
        INNER JOIN academy_training_action AS ata
            ON ata.training_activity_id = atc."id"
        INNER JOIN academy_training_action_enrolment AS tae
            ON tae.training_action_id = ata."id"
        WHERE ata.active AND atc.active AND acu.active

    ), training_modules AS (

        SELECT DISTINCT
            tta."id" AS assignment_id,
            tta.training_ref,
            tae.student_id
        FROM
            academy_tests_test_training_assignment AS tta
        INNER JOIN academy_training_module_tree_readonly AS tree
            ON tree.requested_module_id = tta."training_module_id"
        INNER JOIN academy_training_module AS atm
            ON atm."id" = tree.responded_module_id
        INNER JOIN academy_competency_unit AS acu
            ON acu.training_module_id = atm."id"
        INNER JOIN academy_training_activity AS atc
            ON atc."id" = acu.training_activity_id
        INNER JOIN academy_training_action AS ata
            ON ata.training_activity_id = atc."id"
        INNER JOIN academy_training_action_enrolment AS tae
            ON tae.training_action_id = ata."id"
        WHERE ata.active AND atc.active AND acu.active AND atm.active

    )
    SELECT assignment_id, student_id FROM training_enrolments UNION ALL
    SELECT assignment_id, student_id FROM training_actions UNION ALL
    SELECT assignment_id, student_id FROM training_activities UNION ALL
    SELECT assignment_id, student_id FROM competency_units UNION ALL
    SELECT assignment_id, student_id FROM training_modules
'''



# Many2manyThroughView:
# Allow to recursive get enrolment related items
# -----------------------------------------------------------------------------
ACADEMY_TRAINING_AVAILABLE_ITEMS_REL = '''
    WITH enrolments AS (
        SELECT
            tae."id" AS enrolment_id,
            ass."id" AS related_id
        FROM
            academy_training_action_enrolment AS tae
            INNER JOIN academy_action_enrolment_competency_unit_rel AS rel
                ON rel.action_enrolment_id = tae."id"
            INNER JOIN {related} AS ass
                ON ass.enrolment_id = tae."id" AND (
                    ass.secondary_id IS NULL OR
                    ass.secondary_id = rel.competency_unit_id
                )
    ), actions AS(
        SELECT
            tae."id" AS enrolment_id,
            ass."id" AS related_id
        FROM
            academy_training_action_enrolment AS tae
            INNER JOIN academy_action_enrolment_competency_unit_rel AS rel
                ON rel.action_enrolment_id = tae."id"
            INNER JOIN academy_training_action AS ata
                ON ata."id" = tae.training_action_id
            INNER JOIN {related} AS ass
                ON ass.training_action_id = ata."id" AND (
                    ass.secondary_id IS NULL OR
                    ass.secondary_id = rel.competency_unit_id
                )
            WHERE ata.active IS TRUE
    ), activities AS (
        SELECT
            tae."id" AS enrolment_id,
            ass."id" AS related_id
        FROM
            academy_training_action_enrolment AS tae
            INNER JOIN academy_action_enrolment_competency_unit_rel AS rel
                ON rel.action_enrolment_id = tae."id"
            INNER JOIN academy_training_action AS ata
                ON ata."id" = tae.training_action_id
            inner join academy_training_activity AS atc
                ON atc."id" = ata.training_activity_id
            INNER JOIN {related} AS ass
                ON ass.training_activity_id = atc."id" AND (
                    ass.secondary_id IS NULL OR
                    ass.secondary_id = rel.competency_unit_id
                )
            WHERE ata.active IS TRUE AND atc.active IS TRUE
    )
    , competencies AS (
        SELECT
            tae."id" AS enrolment_id,
            ass."id" AS related_id
        FROM
            academy_training_action_enrolment AS tae
            INNER JOIN academy_action_enrolment_competency_unit_rel AS rel
                ON rel.action_enrolment_id = tae."id"
            INNER JOIN academy_competency_unit AS acu
                ON acu."id" = rel.competency_unit_id
            INNER JOIN {related} AS ass
                ON ass.competency_unit_id = acu."id"
            WHERE acu.active IS TRUE
    ), modules AS (
      SELECT
            tae."id" AS enrolment_id,
            ass."id" AS related_id
        FROM
            academy_training_action_enrolment AS tae
            INNER JOIN academy_action_enrolment_competency_unit_rel AS rel
                ON rel.action_enrolment_id = tae."id"
            INNER JOIN academy_competency_unit AS acu
                ON acu."id" = rel.competency_unit_id
            INNER JOIN academy_training_module_tree_readonly AS tree
                ON tree.requested_module_id = acu.training_module_id
            INNER JOIN academy_training_module AS atm
                ON atm."id" = tree.responded_module_id
            INNER JOIN {related} AS ass
                ON ass."training_module_id" = atm."id"
            WHERE acu.active IS TRUE AND atm.active IS TRUE
    ), training AS (
        SELECT * FROM enrolments UNION DISTINCT
        SELECT * FROM actions UNION DISTINCT
        SELECT * FROM activities UNION DISTINCT
        SELECT * FROM competencies UNION DISTINCT
        SELECT * FROM modules
    ) SELECT * FROM training
'''
