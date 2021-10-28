# -*- coding: utf-8 -*-
""" Raw SQL sentences will be used in inverse search methods

MODEL: academy_tests.model_academy_tests_test_availability
Super relation will be used to list all items from all models in which a test
has been used.
"""

ACADEMY_TESTS_TEST_AVAILABILITY_MODEL = '''
    WITH all_data AS (
        SELECT
            test_id,
            'academy.training.module' :: VARCHAR AS model,
            training_module_id AS res_id
        FROM
            academy_tests_test_training_module_rel UNION
        SELECT
            test_id,
            'academy.competency.unit' :: VARCHAR AS model,
            competency_unit_id AS res_id
        FROM
            academy_tests_test_competency_unit_rel UNION
        SELECT
            test_id,
            'academy.training.activity' :: VARCHAR AS model,
            training_activity_id AS res_id
        FROM
            academy_tests_test_training_activity_rel UNION
        SELECT
            test_id,
            'academy.training.action' :: VARCHAR AS model,
            training_action_id AS res_id
        FROM
            academy_tests_test_training_action_rel UNION
        SELECT
            test_id,
            'academy.training.action.enrolment' :: VARCHAR AS model,
            enrolment_id AS res_id
        FROM
            academy_tests_test_training_action_enrolment_rel
    )
    SELECT
        ROW_NUMBER() OVER()::INTEGER AS "id",
        1::INTEGER AS create_uid,
        1::INTEGER AS write_uid,
        CURRENT_TIMESTAMP AS create_date,
        CURRENT_TIMESTAMP AS write_date,
        test_id,
        model,
        res_id,
        (model || ',' || res_id)::VARCHAR AS related_id
    FROM all_data
'''
