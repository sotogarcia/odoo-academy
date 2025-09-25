# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request, Response
from odoo.http import content_disposition

from odoo.tools.translate import _

import xml.etree.cElementTree as ET
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


ID_TRAINING_ACTIVITY_FIELD_MAP = {
    "code": "code",
    "name": "name",
    "description": "description",
    "available_time": "available_time",
    "general_competence": "general_competence",
    "professional_area_id": "professional_area",
    "qualification_level_id": "qualification_level",
    "professional_family_id": "professional_family",
    "professional_field_id": "professional_field",
}

ID_COMPETENY_UNIT_FIELD_MAP = {
    "code": "code",
    "name": "name",
    "description": "description",
}

ID_TRAINING_MODULE_FIELD_MAP = {
    "code": "code",
    "name": "name",
    "description": "description",
}


class Publish(http.Controller):
    def xml_item_ids(self, et, tag, target, child_tag=False, child_map=None):
        count = str(len(target))

        new_et = ET.SubElement(et, tag, count=count)

        if target and child_tag:
            for item in target:
                self.xml_item_id(new_et, child_tag, item, child_map)

        return new_et

    def xml_item_id(self, et, tag, item, field_map=None):
        field_map = field_map or {"name": "name"}

        id_val = str(item.id)
        act = str(int(getattr(item, "active", True)))

        upd = item.write_date or datetime.now()
        upd = str(upd.strftime("%m/%d/%Y %H:%M:%S"))

        target = ET.SubElement(et, tag, id=id_val, active=act, updated=upd)

        for field_name, node_name in field_map.items():
            value = getattr(item, field_name, None) or ""
            if field_name[-3:] == "_id" and value:
                self.xml_item_id(target, node_name, value)
            else:
                ET.SubElement(target, node_name).text = str(value)

        return target

    def _serialize_activity(self, parent, activity_id):
        activity_obj = request.env["academy.training.activity"]

        activity = activity_obj.browse(activity_id)

        act_et = self.xml_item_id(
            parent, "activity", activity, ID_TRAINING_ACTIVITY_FIELD_MAP
        )

        sectors = activity.professional_sector_ids
        self.xml_item_ids(
            act_et, "professional_sectors", sectors, "professional_sector"
        )

        cunits = activity.competency_unit_ids
        cus_et = self.xml_item_ids(act_et, "competency_units", cunits)

        for cu in activity.competency_unit_ids:
            cu_et = self.xml_item_id(
                cus_et, "competency", cu, ID_COMPETENY_UNIT_FIELD_MAP
            )

            mod = cu.training_module_id
            mod_et = self.xml_item_id(
                cu_et, "module", mod, ID_TRAINING_MODULE_FIELD_MAP
            )

            tunits = mod.training_unit_ids
            tus_et = self.xml_item_ids(mod_et, "training_units", tunits)
            for tu in mod.training_unit_ids:
                self.xml_item_id(
                    tus_et, "unit", tu, ID_TRAINING_MODULE_FIELD_MAP
                )

    def _serialize_action(self, parent, action_id):
        action_obj = request.env["academy.training.action"]

        action = action_obj.browse(action_id)

        act_et = self.xml_item_id(
            parent, "action", action, ID_TRAINING_ACTIVITY_FIELD_MAP
        )

        sectors = action.professional_sector_ids
        self.xml_item_ids(
            act_et, "professional_sectors", sectors, "professional_sector"
        )

        cunits = action.competency_unit_ids
        cus_et = self.xml_item_ids(act_et, "competency_units", cunits)

        for cu in action.competency_unit_ids:
            cu_et = self.xml_item_id(
                cus_et, "competency", cu, ID_COMPETENY_UNIT_FIELD_MAP
            )

            mod = cu.training_module_id
            mod_et = self.xml_item_id(
                cu_et, "module", mod, ID_TRAINING_MODULE_FIELD_MAP
            )

            tunits = mod.training_unit_ids
            tus_et = self.xml_item_ids(mod_et, "training_units", tunits)
            for tu in mod.training_unit_ids:
                self.xml_item_id(
                    tus_et, "unit", tu, ID_TRAINING_MODULE_FIELD_MAP
                )

    @http.route(
        "/academy_catalog/activity/<activity_id>", type="http", auth="public"
    )
    def activity(self, **kw):
        activity_id = int(kw["activity_id"])

        headers = [
            ("Content-Type", "application/xml"),
            ("Content-Disposition", "inline"),
        ]

        root = ET.Element("catalog")

        self._serialize_activity(root, activity_id)

        xml = ET.tostring(root, encoding="utf8", method="xml")

        return request.make_response(xml, headers=headers)

    @http.route("/academy_catalog/activity/all", type="http", auth="public")
    def activities(self, **kw):
        activity_obj = request.env["academy.training.activity"]
        activity_set = activity_obj.search([])

        headers = [
            ("Content-Type", "application/xml"),
            ("Content-Disposition", "inline"),
        ]

        root = ET.Element("catalog")

        fmap = {"code": "code", "name": "name", "description": "description"}
        self.xml_item_ids(root, "activities", activity_set, "activity", fmap)

        xml = ET.tostring(root, encoding="utf8", method="xml")

        return request.make_response(xml, headers=headers)

    @http.route(
        "/academy_catalog/action/<action_id>", type="http", auth="public"
    )
    def action(self, **kw):
        action_id = int(kw["action_id"])

        headers = [
            ("Content-Type", "application/xml"),
            ("Content-Disposition", "inline"),
        ]

        root = ET.Element("catalog")

        self._serialize_action(root, action_id)

        xml = ET.tostring(root, encoding="utf8", method="xml")

        return request.make_response(xml, headers=headers)

    @http.route("/academy_catalog/action/all", type="http", auth="public")
    def activities(self, **kw):
        action_obj = request.env["academy.training.action"]
        action_set = action_obj.search([])

        headers = [
            ("Content-Type", "application/xml"),
            ("Content-Disposition", "inline"),
        ]

        root = ET.Element("catalog")

        fmap = {
            "action_code": "code",
            "name": "name",
            "description": "description",
        }
        self.xml_item_ids(root, "actions", action_set, "action", fmap)

        xml = ET.tostring(root, encoding="utf8", method="xml")

        return request.make_response(xml, headers=headers)
