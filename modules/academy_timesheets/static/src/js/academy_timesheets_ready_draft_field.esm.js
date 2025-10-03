// Ready/Draft selection field (Odoo 18, OWL + ES Modules)
//
// This field extends the default selection behavior to display a colored
// "status pill" (green for 'ready', red for 'draft') and a dropdown with the
// remaining choices. It reads optional legend fields from the record:
//   - legend_ready
//   - legend_draft
//   - legend_normal
//
// Usage in views (field attribute):
//   widget="ready_draft_widget"
//
// Notes:
// - No jQuery/underscore, pure OWL bindings.
// - Uses standard field props; call `this.props.update(value)` to write.
// - Readonly handled via `this.props.readonly`.

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

const fieldRegistry = registry.category("fields");

export class ReadyDraftField extends Component {
  static template = "academy_timesheets.ReadyDraftField";
  static props = {
    ...standardFieldProps,
    // Standard selection definition comes from `props.field.selection`.
  };

  /**
   * Compute dropdown items from selection and record legends.
   * Returns array of: { name, label, cssClass }
   */
  get states() {
    const sel = this.props.field.selection || [];
    const data = this.props.record.data || {};

    const legendReady =
      data.legend_ready ? String(data.legend_ready) : undefined;
    const legendDraft =
      data.legend_draft ? String(data.legend_draft) : undefined;
    const legendNormal =
      data.legend_normal ? String(data.legend_normal) : undefined;

    const items = sel.map(([value, label]) => {
      const res = { name: String(value), label: String(label) };
      if (value === "ready") {
        res.cssClass = "o_status_green";
        res.label = legendReady || res.label;
      } else if (value === "draft") {
        res.cssClass = "o_status_red";
        res.label = legendDraft || res.label;
      } else {
        res.cssClass = "";
        res.label = legendNormal || res.label;
      }
      return res;
    });

    return items;
  }

  /**
   * Currently selected state object, or the first option as fallback.
   */
  get currentState() {
    const cur = this.states.find((s) => s.name === this.props.value);
    return cur || this.states[0];
  }

  /**
   * States to show in the dropdown (exclude the current one).
   */
  get otherStates() {
    const cur = this.currentState?.name;
    return this.states.filter((s) => s.name !== cur);
  }

  /**
   * ARIA label for the button: "<Field String>: <Current Label>"
   */
  get ariaLabel() {
    const fieldLabel = this.props.string || "";
    const stateLabel = this.currentState ? this.currentState.label : "";
    return `${fieldLabel}: ${stateLabel}`;
  }

  /**
   * Write selected value to the record.
   */
  onSelect(value) {
    if (!this.props.readonly) {
      this.props.update(value);
    }
  }
}

fieldRegistry.add("ready_draft_widget", {
  component: ReadyDraftField,
  supportedTypes: ["selection"],
});

export default ReadyDraftField;
