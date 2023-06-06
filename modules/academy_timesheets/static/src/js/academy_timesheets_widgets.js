odoo.define('academy_timesheets.field_widgets', function (require) {
"use strict";

var AbstractField = require('web.AbstractField');
var fieldRegistry = require('web.field_registry');

var core = require('web.core');
var qweb = core.qweb;

/**
 * This module contains most of the basic (meaning: non relational) field
 * widgets. Field widgets are supposed to be used in views inheriting from
 * BasicView, so, they can work with the records obtained from a BasicModel.
 */


var ReadyDraftWidget = AbstractField.extend({
    template: 'ReadyDraftFormSelection',

    events: {
        'click .dropdown-item': '_setSelection',
    },

    supportedFieldTypes: ['selection'],

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * Returns the drop down button.
     *
     * @override
     */
    getFocusableElement: function () {
        return this.$("a[data-toggle='dropdown']");
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Prepares the state values to be rendered using the FormSelection.Items template.
     *
     * @private
     */
    _prepareDropdownValues: function () {
        var self = this;
        var _data = [];
        var current_stage_id = self.recordData.stage_id && self.recordData.stage_id[0];

        var stage_data = {
            id: current_stage_id,
            legend_ready: this.recordData.legend_ready || undefined,
            legend_draft : this.recordData.legend_draft || undefined,
        };

        _.map(this.field.selection || [], function (selection_item) {
            var value = {
                'name': selection_item[0],
                'tooltip': selection_item[1],
            };
            if (selection_item[0] === 'ready') {
                value.state_class = 'o_status_green';
                value.state_name = stage_data.legend_ready ? stage_data.legend_ready : selection_item[1];
            } else if (selection_item[0] === 'draft') {
                value.state_class = 'o_status_red';
                value.state_name = stage_data.legend_draft ? stage_data.legend_draft : selection_item[1];
            } else {
                value.state_name = stage_data.legend_normal ? stage_data.legend_normal : selection_item[1];
            }

            _data.push(value);

        });

        return _data;
    },

    /**
     * This widget uses the FormSelection template but needs to customize it a bit.
     *
     * @private
     * @override
     */
    _render: function () {
        var states = this._prepareDropdownValues();
        // Adapt "FormSelection"
        // Like priority, default on the first possible value if no value is given.
        var currentState = _.findWhere(states, {name: this.value}) || states[0];
        this.$('.o_status')
            .removeClass('o_status_red o_status_green')
            .addClass(currentState.state_class)
            .prop('special_click', true)
            .parent().attr('title', currentState.state_name)
            .attr('aria-label', this.string + ": " + currentState.state_name);

        // Render "FormSelection.Items" and move it into "FormSelection"
        var $items = $(qweb.render('ReadyDraftFormSelection.items', {
            states: _.without(states, currentState)
        }));
        var $dropdown = this.$('.dropdown-menu');
        $dropdown.children().remove(); // remove old items
        $items.appendTo($dropdown);

        // Disable edition if the field is readonly
        var isReadonly = this.record.evalModifiers(this.attrs.modifiers).readonly;
        this.$('a[data-toggle=dropdown]').toggleClass('disabled', isReadonly || false);
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Intercepts the click on the FormSelection.Item to set the widget value.
     *
     * @private
     * @param {MouseEvent} ev
     */
    _setSelection: function (ev) {
        ev.preventDefault();
        var $item = $(ev.currentTarget);
        var value = String($item.data('value'));
        this._setValue(value);
        if (this.mode === 'edit') {
            this._render();
        }
    }
});

fieldRegistry.add('ready_draft_widget', ReadyDraftWidget);

return ReadyDraftWidget;

});