import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { CharField } from "@web/views/fields/char/char_field";

export class UrlTruncatedField extends Component {
  static template = "civil_service_tracker.UrlTruncatedField";
  static props = { ...standardFieldProps };
  static components = { CharField };
}

export const urlTruncatedField = {
  component: UrlTruncatedField,
  supportedTypes: ["char"],
};

registry.category("fields").add("url_truncated", urlTruncatedField);
