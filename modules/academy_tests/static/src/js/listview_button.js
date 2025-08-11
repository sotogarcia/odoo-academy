odoo.define('academy_tests.all_header_buttons', function (require) {
    "use strict";

    var core = require('web.core');
    var QWeb = core.qweb;

    var KanbanController = require("web.KanbanController");
    var ListController = require("web.ListController");

    var IncludeCustomButtons = {
        renderButtons: function () {
            this._super.apply(this, arguments);

            if (!this.$buttons) {
                return;
            }

            const view_type = this.viewType;
            const is_kanban_or_list = view_type === 'kanban' || view_type === 'list';
            const template_prefix = view_type === 'kanban' ? 'KanbanView.buttons.' : 'ListView.buttons.';

            const buttons = [
                {
                    model: 'academy.tests.random.template',
                    id: '11B3838D16FB4B5F8814077387FCAF3C',
                    template: 'create_template_from_training',
                    handler: '_create_template_from_training'
                    // args: ['A']  // optional
                },
                {
                    model: 'academy.tests.test.question.rel',
                    id: '3E46E901F83C4EABB2364AA81B29327B',
                    template: 'open_shuffle_wizard',
                    handler: '_open_shuffle_wizard'
                    // args: ['A']  // optional
                }
            ];

            buttons.forEach(btn => {
                if (
                    this.modelName === btn.model &&
                    is_kanban_or_list &&
                    !this.$buttons.find('#' + btn.id).length
                ) {
                    const template_name = template_prefix + btn.template;
                    const $element = this.$buttons.last().find('button:last');

                    if ($element.length === 1) {
                        const $custom = $(QWeb.render(template_name));
                        $element.after($custom);

                        const $btn = this.$buttons.find('#' + btn.id);
                        const handler = this[btn.handler];

                        if (btn.args) {
                            $btn.on('click', () => handler.apply(this, btn.args));
                        } else {
                            $btn.on('click', this.proxy(handler));
                        }
                    }
                }
            });
        },

        _create_template_from_training: function () {
            const data = this.model.get(this.handle);
            const training_ref = data.context['default_training_ref'];

            return this.do_action({
                type: "ir.actions.act_window",
                name: "Choose type",
                res_model: "academy.tests.random.template.type.wizard",
                views: [[false, 'form']],
                target: 'new',
                context: {'training_ref': training_ref},
                flags: {
                    form: {
                        action_buttons: true,
                        options: {mode: 'edit'}
                    }
                }
            });
        },

        _open_shuffle_wizard: function (type) {
            const data = this.model.get(this.handle);
            const test_id = data.context['default_test_id'];

            return this.do_action({
                type: "ir.actions.act_window",
                name: "Shuffle questions",
                res_model: "academy.tests.test.question.shuffle.wizard",
                views: [[false, 'form']],
                target: 'new',
                context: {
                    'default_test_id': test_id,
                    'shuffle_type': type
                },
                flags: {
                    form: {
                        action_buttons: true,
                        options: {mode: 'edit'}
                    }
                }
            });
        }
    };

    KanbanController.include(IncludeCustomButtons);
    ListController.include(IncludeCustomButtons);
});
