odoo.define('academy_tests.listview_button', function (require) {
    "use strict";

    var KanbanController = require("web.KanbanController");
    var ListController = require("web.ListController");

    var IncludeListView = {
        renderButtons: function() {
            var expected = "academy.tests.random.template";

            this._super.apply(this, arguments);

            if (this.hasButtons && this.modelName === expected) {
                var summary_apply_leave_btn = this.$buttons.find(
                    'button.o_create_template_from_training');
                summary_apply_leave_btn.on(
                    'click', this.proxy('create_template_from_training'));

                // Patch: the o_button_import was appearing duplicated
                if (this.viewType === 'kanban') {
                    this.$buttons.find('button.o_button_import').hide();
                }
            }
        },

        activateTemplateBaseButton: function() {
            return this.isExpectedModel() && this.hasDefaultTrainingRef();
        },

        isExpectedModel: function() {
            return this.modelName =='academy.tests.random.template';
        },

        hasDefaultTrainingRef: function() {
            var data = this.model.get(this.handle);
            return 'context' in data && 'default_training_ref' in data.context;
        },

        getDefaultTrainingRef: function() {
            var data = this.model.get(this.handle);
            return data.context['default_training_ref'];
        },


        create_template_from_training: function() {
            var self = this;

            var training_ref = self.getDefaultTrainingRef()

            /* this._rpc({
                model: 'academy.tests.random.template',
                method: 'template_for_training',
                args: [training_ref],
            }).then(function (result) {
                self.do_action(result);
            });*/

            var self = this;
            var action = {
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