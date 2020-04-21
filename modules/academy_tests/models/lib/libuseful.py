# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" SQL

This module contains the sql used in some custom views
"""


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
