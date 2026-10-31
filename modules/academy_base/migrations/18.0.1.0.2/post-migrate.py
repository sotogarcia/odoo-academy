"""Retire incorrectly mixed educational and professional qualification levels.

The previous catalog mixed ISCED programme levels, Spanish programme types,
and fictitious professional certificate levels 4-8. Archive these records
without unlinking them: they may be referenced by existing programmes or
professional qualifications. Keep stable XML IDs for the valid levels 1-3.
"""

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

RETIRED_XML_IDS = (
    *(f"academy_qualification_level_level_isced_2011_{i}" for i in range(10)),
    "academy_qualification_level_es_3B",
    "academy_qualification_level_es_3C",
    "academy_qualification_level_es_3D",
    *(f"academy_qualification_level_0{i}" for i in range(4, 9)),
)

OLD_DESCRIPTIONS = {
    1: "Basic general knowledge",
    2: "Basic factual knowledge in a specific field of work or study",
    3: (
        "Knowledge of facts, principles, processes and general concepts "
        "in a field of work or concrete study"
    ),
}


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    model = env["academy.qualification.level"].with_context(active_test=False)

    retired = 0
    for xml_id in RETIRED_XML_IDS:
        record = env.ref(f"academy_base.{xml_id}", raise_if_not_found=False)
        if record and record.exists():
            record.active = False
            retired += 1

    for level in (1, 2, 3):
        record = env.ref(
            f"academy_base.academy_qualification_level_0{level}",
            raise_if_not_found=False,
        )
        if not record or not record.exists():
            continue

        code = f"FP-{level}"
        conflict = model.search(
            [("code", "=", code), ("id", "!=", record.id)],
            limit=1,
        )
        if conflict:
            raise ValueError(
                f"Cannot normalize qualification level {level}: "
                f"code {code} is already used by record {conflict.id}."
            )

        # Preserve edited names and descriptions of noupdate seed records.
        record = record.with_context(lang="en_US")
        values = {"code": code, "sequence": level * 10}
        if record.name == f"Professional Certificate - Level {level}":
            values["name"] = f"Professional qualification - Level {level}"
        if record.description == OLD_DESCRIPTIONS[level]:
            values["description"] = (
                f"Professional qualification level {level} in the "
                "Spanish Vocational Education and Training System."
            )
        record.write(values)

    _logger.info(
        "Qualification levels normalized; retired %s legacy level records "
        "without deleting historical references.",
        retired,
    )
