// in file academy_tests.js
odoo.define('academy_tests.QuestionKanbanView', function(require) {
    "use strict";

    var KanbanRecord = require('web.KanbanRecord');

    /*
    * Captures question kanban click event when target is the menu button and
    * prevents default code exetution.
    */
    KanbanRecord.include({

        events: _.defaults({
            'click .o_question_kanban_status_bar': '_onKanbanStatusMenuClick',
            'click #question_kanban_status_menu_add_to_test': '_onKanbanStatusMenuAddToTest',
            'click a[data-markdown]': '_onKanbanDataMarkdown',
        }, KanbanRecord.prototype.events),

        _onKanbanStatusMenuClick: function(event) {
            event.preventDefault();
        },

        _onKanbanStatusMenuAddToTest: function(event) {
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
                this.do_action({
                    type: 'ir.actions.act_window',
                    res_model: 'academy.tests.question.append.wizard',
                    views: [[false, 'form']],
                    target: 'new',
                    context: {'default_question_ids': [(4, question_id)]}
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


