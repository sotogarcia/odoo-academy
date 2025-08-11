odoo.define('civil_service_tracker.header_view_buttons', function (require) {
    "use strict";

    var core = require('web.core');
    var QWeb = core.qweb;
    var session = require('web.session');

    var ListController = require("web.ListController");
    var CalendarController = require("web.CalendarController");

    var IncludeCustomButtonsView = {
        renderButtons: function ($node) {
            this._super.apply(this, arguments);

            if (this.$buttons && this.cstModelMatches()) {
                this.cstTryToAppendCustomButton();
            }
        },

        cstModelMatches: function() {
            return this.modelName == 'civil.service.tracker.process.event';
        },

        cstTryToAppendCustomButton: function() {
            let template = false;
            let selector = false;

            switch(this.viewType) {
                case 'list':
                    template = 'ListView.buttons.quick_create_public_offer';
                    selector = 'button:last';
                    this.cstAppendCustomButton(selector, template);
                    break;

                case 'calendar':
                    template = 'CalendarView.buttons.quick_create_public_offer';
                    selector = '> div.btn-group:last';
                    this.cstAppendCustomButton(selector, template);
                    break;
            } // switch
        },

        cstAppendCustomButton: function(selector, template) {
            let element = this.$buttons.find(selector);
            let custom = null;

            if(element.length === 1) {
                custom = $(QWeb.render(template));
                custom = element.after(custom);

                this.cstListenForClickEvent();
            }

            return custom;
        },

        cstListenForClickEvent: function(event) {
            let selector = '#962896B6DEF44805A7C408C5A6619DA3';
            let button = this.$buttons.find(selector);

            button.on('click', this.proxy('cstShowWizard'));
        },

        cstShowWizard: function(event) {

            var action = {
                type: "ir.actions.act_window",
                name: "Quick create offer",
                res_model: "civil.service.tracker.quick.offer.wizard",
                views: [[false,'form']],
                target: 'new',
                view_mode : 'form',
                context: this.initialState.context,
                flags: {'form': {'action_buttons': true, 'options': {'mode': 'edit'}}}
            };

            return this.do_action(action);
        },

    };

    ListController.include(IncludeCustomButtonsView);
    CalendarController.include(IncludeCustomButtonsView);

});
