# -*- coding: utf-8 -*-
""" Raw SQL sentences will be used in inverse search methods
"""

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
