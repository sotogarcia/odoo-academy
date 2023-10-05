odoo.define('academy_timesheets_to_calendar.header_view_buttons', function (require) {
    "use strict";

    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;

    var CalendarController = require("web.CalendarController");

    var IncludeToCalendarButtonsView = {
        renderButtons: function ($node) {
            this._super.apply(this, arguments);

            let model = 'academy.training.session';
            let btn_id = '#74E845E2BD7943AABA2A2C0D672F4637';
            let template = 'syncronize_with_calendar';
            let method = this.proxy('toCalendarSyncronizeWithCalendar');
            if (this.toCalendarModelMatches(model) && this.toCalendarNeedAButton(btn_id)) {
                this.toCalendarTryToAppendCustomButton(template, btn_id, method);
            }

        },

        toCalendarModelMatches: function(model) {
            return this.modelName == model;
        },

        toCalendarNeedAButton: function(btn_id) {
            return this.context['active_model'] === 'academy.teacher' &&
                   this.$buttons && !this.$buttons.find(btn_id).length;
        },

        toCalendarTryToAppendCustomButton: function(template, btn_id, method) {
            let selector = false;

            switch(this.viewType) {

                case 'calendar':
                    template = 'CalendarView.buttons.' + template;
                    selector = '> div.btn-group:last';
                    this.toCalendarAppendCustomButton(selector, template, btn_id, method);
                    break;

            } // switch
        },

        toCalendarAppendCustomButton: function(selector, template, btn_id, method) {
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

        toCalendarSyncronizeWithCalendar: function(event) {
            let self = this;

            let viewControllerData = this.model.get(this.handle);
            let scale = viewControllerData['scale'];
            let startDate = viewControllerData['start_date'].format();
            let endDate = viewControllerData['end_date'].format();

            let context = this.context;
            let res_model = null;
            let res_id = null;

            console.log(context);

            if ('default_training_action_id' in context) {
                res_model = 'academy.training.action';
                res_id = context['default_training_action_id'];
            } else if ('default_primary_teacher_id' in context) {
                res_model = 'academy.teacher';
                res_id = context['default_primary_teacher_id'];
            }

            // Llamar al método Python utilizando el mecanismo de RPC
            this._rpc({
                model: 'academy.training.session',
                method: 'btn_syncronize',
                args: [scale, startDate, endDate, res_model, res_id],
            }).then(function(result) {
                return self.do_action({
                    name: _t('Training sessions'),
                    type: 'ir.actions.act_window',
                    res_model: 'calendar.event',
                    views: [[false, 'calendar'], [false, 'list']],
                    target: 'main'
                });

            }).catch(function(error) {
                return core.bus.trigger('notification', 'danger', {
                    title: 'Error',
                    message: error.message,
                    sticky: true,
                });
            });

        },

    }; // IncludeToCalendarButtonsView


    CalendarController.include(IncludeToCalendarButtonsView);

}); // define