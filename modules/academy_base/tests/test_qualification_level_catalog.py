"""Qualification level catalog: professional levels versus educational levels."""

from odoo.tests.common import TransactionCase


class TestQualificationLevelCatalog(TransactionCase):
    def test_professional_qualification_levels(self):
        for level in (1, 2, 3):
            record = self.env.ref(
                f"academy_base.academy_qualification_level_0{level}"
            )
            self.assertTrue(record.active)
            self.assertEqual(record.code, f"FP-{level}")
            self.assertEqual(
                record.name,
                f"Professional qualification - Level {level}",
            )

    def test_legacy_programme_levels_are_archived(self):
        retired_ids = [
            *(f"academy_qualification_level_level_isced_2011_{i}" for i in range(10)),
            "academy_qualification_level_es_3B",
            "academy_qualification_level_es_3C",
            "academy_qualification_level_es_3D",
            *(f"academy_qualification_level_0{i}" for i in range(4, 9)),
        ]
        for xml_id in retired_ids:
            record = self.env.ref(f"academy_base.{xml_id}")
            self.assertFalse(record.active, xml_id)
            # Archived levels must still exist to preserve related records.
            self.assertTrue(record.exists())
