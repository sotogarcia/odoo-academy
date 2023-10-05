odoo.define('academy_tests.listview_button', function (require) {
    "use strict";

    var core = require('web.core');
    var QWeb = core.qweb;

    var KanbanController = require("web.KanbanController");
    var ListController = require("web.ListController");

    var IncludeListView = {
        renderButtons: function() {

            this._super.apply(this, arguments);

            let model = 'academy.tests.random.template';
            let btn_id = '#11B3838D16FB4B5F8814077387FCAF3C';
            let template = 'create_template_from_training';
            let method = this.proxy('create_template_from_training');

            let custom = null;
            let button = null;
            let element = null;
            let selector = null;

            let vt = this.viewType

            if (this.modelName == model && (vt === 'kanban' || vt === 'list')
                && this.$buttons && !this.$buttons.find(btn_id).length)
            {
                switch(this.viewType) {

                    case 'kanban':
                        template = 'KanbanView.buttons.' + template;
                        selector = 'button:last';
                        break;

                    case 'list':
                        template = 'ListView.buttons.' + template;
                        selector = 'button:last';
                        break;
                } // switch

                element = this.$buttons.last().find(selector);

                if(element.length === 1) {
                    custom = $(QWeb.render(template));
                    custom = element.after(custom);

                    button = this.$buttons.find(btn_id);
                    button.on('click', method);
                }

            } // if

        },

        create_template_from_training: function() {
            let self = this;

            let data = this.model.get(this.handle);
            let training_ref = data.context['default_training_ref'];

            let action = {
                type: "ir.actions.act_window",
                name: "Choose type",
                res_model: "academy.tests.random.template.type.wizard",
                views: [[false,'form']],
                target: 'new',
                views: [[false, 'form']],
                view_type : 'form',
                view_mode : 'form',
                context: {'training_ref': training_ref},
                flags: {'form': {'action_buttons': true, 'options': {'mode': 'edit'}}}
            };

            return this.do_action(action);
        },

    };

    KanbanController.include(IncludeListView);
    ListController.include(IncludeListView);
});