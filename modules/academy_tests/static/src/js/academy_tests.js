// in file academy_tests.js
odoo.define('academy_tests.QuestionKanbanView', function(require) {
    "use strict";

    var KanbanRecord = require('web.KanbanRecord');
    var rpc = require('web.rpc')

    /*
    * Captures question kanban click event when target is the menu button and
    * prevents default code exetution.
    */
    KanbanRecord.include({

        events: _.defaults({
            'click .o_question_kanban_status_bar': '_onKanbanStatusMenuClick',
            'click .question_kanban_manually_append_cmd': '_onQuestionKanbanManuallyAppendCmd',
            'click a[data-markdown]': '_onKanbanDataMarkdown',
        }, KanbanRecord.prototype.events),

        init: function (parent, options) {
            this._super.apply(this, arguments);
        },

        start: function() {
            this._super.apply(this, arguments);

            if(this.modelName === 'academy.tests.question') {
                if(this.record.link_id.raw_value) {
                    this.$el.css('background-color', 'LightBlue');
                }
            }

            if(this.modelName === 'academy.tests.test.question.rel') {
                if(this.record.link_id.raw_value) {
                    this.$el.css('background-color', 'LightBlue');
                }
            }
        },

        _onKanbanStatusMenuClick: function(event) {
            event.preventDefault();
        },

        _switchButtonAspect: function(append) {
            let self = this;
            let i = self.$el.find('i.fa')


            if (append !== false) {
                self.$el.css('background-color', 'LightBlue');
                i.removeClass('fa-plus-square');
                i.removeClass('text-primary');
                i.addClass('fa-minus-square');
                i.addClass('text-danger');
            } else {
                i.removeClass('fa-minus-square');
                i.removeClass('text-danger');
                i.addClass('fa-plus-square');
                i.addClass('text-primary');
                self.$el.css('background-color', 'initial');
            }
        },

        _onQuestionKanbanManuallyAppendCmd: function(event) {
            let self = this;
            let data = this.recordData;
            let question_id = false;

            event.preventDefault();

            if(this.modelName == "academy.tests.test.question.rel") {
                question_id = data.question_id.res_id;
            } else {
                question_id = data['id'];
            }

            if(question_id !== false) {
                rpc.query({
                    model: 'academy.tests.question',
                    method: 'manually_append_to_test',
                    args: [question_id],
                    context: self.state.context
                }).then(function (result) {
                    self._switchButtonAspect(result);
                });
            } // if

        },

        _onKanbanDataMarkdown: function (event) {
            var self = this;
            var data = this.recordData;

            event.preventDefault();

            try {
                var text = jQuery(event.target).data('markdown');
                self._copyStringToClipboard(text);
            } catch(err) {
                console.log('Markdown could no be copied to clipboard')
            }

        },

        _copyStringToClipboard: function (str) {
           var el = document.createElement('textarea');
           el.value = str;
           el.setAttribute('readonly', '');
           el.style = {position: 'absolute', left: '-9999px'};
           document.body.appendChild(el);
           el.select();
           document.execCommand('copy');
           document.body.removeChild(el);
        },

    });

});


odoo.define('html_in_tree_field.web_ext', function (require) {
    "use strict";
    var Listview = require('web.ListView');
    var formats = require('web.formats');

    Listview.Column.include({
        _format: function (row_data, options) {
        // Removed _.escape() function to display html content.
        // Before : return _.escape(formats.format_value(row_data[this.id].value, this, options.value_if_empty));
        return formats.format_value(row_data[this.id].value, this, options.value_if_empty);
        }
    });
});



// in file academy_tests.js
odoo.define('academy_tests.AcademyTestsWidgets', function(require) {

    "use strict";

    var fieldRegistry = require('web.field_registry');
    var AbstractField = require('web.AbstractField');
    var FieldMany2Many = require('web.relational_fields').FieldMany2Many;
    var rpc = require('web.rpc');

    var FieldMany2ManyDeedless = FieldMany2Many.extend({

        events: _.extend({}, AbstractField.prototype.events, {
            'open_record': '_onOpenRecord',
        }),

        init: function (parent, options) {
            this._super.apply(this, arguments);
        },

        /**
         * Prevents odoo form view will be opened for target record
         * @param  {odooevent} event the event data
         */
        _onOpenRecord: function (event) {
            event.stopPropagation();
        },

    }); // FieldMany2ManyMD

    fieldRegistry.add('many2many_deedless', FieldMany2ManyDeedless);
});


odoo.define('AcademyTestsQuestionRelKanbanView.kanban_button', function(require) {
   "use strict";

   var KanbanController = require('web.KanbanController');
   var KanbanView = require('web.KanbanView');
   var viewRegistry = require('web.view_registry');

   var KanbanButton = KanbanController.include({

        buttons_template: 'AcademyTestsQuestionRelKanbanView.button',

        events: _.extend({}, KanbanController.prototype.events, {
           'click .oe_btn_choose_questions': '_ActionChooseQuestions',
        }),

        _ActionChooseQuestions: function () {
            var self = this;

            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'academy.tests.question',
                name :'Choose questions',
                view_mode: 'kanban,tree,form,pivot',
                // view_type: 'form',
                views: [[false, 'kanban'], [false, 'tree'], [false, 'form'], [false, 'pivot']],
                target: 'current',
                res_id: false,
                context: self.initialState.context
            });

        } // _ActionChooseQuestions
   });

   var AcademyTestsQuestionRelKanbanView = KanbanView.extend({
       config: _.extend({}, KanbanView.prototype.config, {
           Controller: KanbanButton
       }),
   });

   viewRegistry.add('button_in_kanban', AcademyTestsQuestionRelKanbanView);
});