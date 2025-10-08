odoo.define('academy_timesheets.header_view_buttons', function (require) {
    "use strict";

    var core = require('web.core');
    var QWeb = core.qweb;
    var session = require('web.session');
    var rpc = require('web.rpc');

    var KanbanController = require("web.KanbanController");
    var ListController = require("web.ListController");
    var CalendarController = require("web.CalendarController");
    var FormController = require("web.FormController");

    var IncludeTimesheetsButtonsView = {
        renderButtons: function ($node) {
            this._super.apply(this, arguments);

            let model = 'academy.teacher';
            let btn_id = '#D73FB1B7653A45DA8A72F768C7436A78';
            let template = 'search_available_teacher';
            let method = this.proxy('timesheetsShowTeacherWizard');
            if (this.timesheetsModelMatches(model) && this.timesheetsNeedAButton(btn_id)) {
                this.timesheetsTryToAppendCustomButton(template, btn_id, method);
            }

        },

        timesheetsModelMatches: function(model) {
            return this.modelName == model;
        },

        timesheetsNeedAButton: function(btn_id) {
            return this.$buttons && !this.$buttons.find(btn_id).length;
        },

        timesheetsTryToAppendCustomButton: function(template, btn_id, method) {
            let selector = false;

            switch(this.viewType) {
                case 'list':
                    template = 'ListView.buttons.' + template;
                    selector = 'button:last';
                    this.timesheetsAppendCustomButton(selector, template);
                    break;

                case 'kanban':
                    template = 'KanbanView.buttons.' + template;
                    selector = 'button:last';
                    this.timesheetsAppendCustomButton(selector, template, btn_id, method);
                    break;

                case 'calendar':
                    template = 'CalendarView.buttons.' + template;
                    selector = '> div.btn-group:last';
                    this.timesheetsAppendCustomButton(selector, template, btn_id, method);
                    break;

                /*case 'form':
                    template = 'FormView.buttons.' + template;
                    selector = 'button:last';
                    this.timesheetsAppendCustomButton(selector, template, btn_id, method);
                    break;*/

            } // switch
        },

        timesheetsAppendCustomButton: function(selector, template, btn_id, method) {
            let element = this.$buttons.last().find(selector);
            let custom = null;
            let button = null;

            if(element.length === 1) {
                custom = $(QWeb.render(template));
                custom = element.after(custom);

                button = this.$buttons.find(btn_id);
                button.on('click', method);
            }

            return custom;
        },

        timesheetsShowTeacherWizard: function(event) {

            var action = {
                type: "ir.actions.act_window",
                name: "Search available",
                res_model: "academy.timesheets.search.teachers.wizard",
                views: [[false,'form']],
                target: 'new',
                views: [[false, 'form']],
                view_type : 'form',
                view_mode : 'form',
                context: this.initialState.context,
                flags: {'form': {'action_buttons': true, 'options': {'mode': 'edit'}}}
            };

            return this.do_action(action);
        },

    };

    KanbanController.include(IncludeTimesheetsButtonsView);
    ListController.include(IncludeTimesheetsButtonsView);
    CalendarController.include(IncludeTimesheetsButtonsView);


    var IncludeTimesheetsFormButtonsView = {
        renderButtons: function ($node) {
            this._super.apply(this, arguments);

            let template = 'search_available_teacher';
            let btn_id = '#D73FB1B7653A45DA8A72F768C7436A78';
            let method = this.proxy('timesheetsFormShowTeacherWizard');
            if (this.timesheetsFormModelMatches() && this.timesheetsFormNeedAButton(btn_id)) {
                this.timesheetsFormTryToAppendCustomButton(template, btn_id, method);
            }

            template = 'search_available_facility';
            btn_id = '#1761B26600AA42ACBA75199632F4DCE0';
            method = this.proxy('timesheetsFormShowFacilityWizard');
            if (this.timesheetsFormModelMatches() && this.timesheetsFormNeedAButton(btn_id)) {
                this.timesheetsFormTryToAppendCustomButton(template, btn_id, method);
            }

        },

        timesheetsFormModelMatches: function() {
            return this.modelName == 'academy.training.session';
        },

        timesheetsFormNeedAButton: function(btn_id) {
            return this.$buttons && !this.$buttons.find(btn_id).length;
        },

        timesheetsFormTryToAppendCustomButton: function(template, btn_id, method) {
            let selector = false;

            if (this.viewType == 'form') {
                template = 'FormView.buttons.' + template;
                selector = 'button:last';
                this.timesheetsFormAppendCustomButton(selector, template, btn_id, method);
            }
        },

        timesheetsFormAppendCustomButton: function(selector, template, btn_id, method) {
            let element = this.$buttons.last().find(selector);
            let custom = null;
            let button = null;

            if(element.length === 1) {
                custom = $(QWeb.render(template));
                custom = element.after(custom);

                button = this.$buttons.find(btn_id);
                button.on('click', method);
            }

            return custom;
        },

        timesheetsFormShowTeacherWizard: function(event) {

            var self = this;

            return rpc.query({
                model: 'academy.training.session',
                method: 'wizard_search_for_available_teachers',
                args: [],
            }).then(function(result) {
                self.do_action(result);
            });

        },

        timesheetsFormShowFacilityWizard: function(event) {
            var self = this;

            return rpc.query({
                model: 'academy.training.session',
                method: 'wizard_search_for_available_facilities',
                args: [],
            }).then(function(result) {
                self.do_action(result);
            });

        },

    };

    FormController.include(IncludeTimesheetsFormButtonsView);

});
