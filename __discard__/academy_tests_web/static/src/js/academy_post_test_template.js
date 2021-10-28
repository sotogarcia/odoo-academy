$(document).ready(function(){

    $('head').append('<link rel="stylesheet" type="text/css" href="/academy_tests_web/static/src/css/academy_post_test_template.css">');
});


odoo.define('academy_tests_web.service', function (require) {

    var utils = require('web.utils');
    var rpc = require('web.rpc');
    var core = require('web.core');
    var website = require('website.website'); // The important line
    var session = require('web.session');

    /* bind double click and single click separately */
    var DELAY = 250, clicks = 0, timer = null;
    var QWeb = core.qweb;


    /*-- Question class
    ------------------------------------------------------------------------*/
    var AtQuestion = core.Class.extend({
        obj : null,

        /** Main class methods
        ---------------------------------------------------------------------*/

        init : function(academy_test_question) {
            /*-- STEP 1: Initialice this object variables -- */
            obj = this;

            obj.bind_events(academy_test_question);

        },

        bind_events : function(academy_test_question) {
            /*-- STEP 2: Initialice Bootstrap javascript elements -- */
            jQuery(academy_test_question).find('[data-toggle="popover"]').popover({container: 'body'});

            /*-- STEP 2: Bind button events --
                 not needed for impugment and information buttons*/
            jQuery(academy_test_question).find('.btn-edit-question').on("click", obj.on_btn_edit_question_click);
            jQuery(academy_test_question).find('.btn-revise-question').on("click", obj.on_btn_revise_question_click);
            jQuery(academy_test_question).find('.btn-revise-question').on("dblclick", obj.on_btn_revise_question_dblclick);

            jQuery(academy_test_question).find('a.ir-attachment-image-datas').on("click", obj.on_ir_attachment_image_datas);

            jQuery(academy_test_question).find('.btn-edit-question-backend').on("click", obj.on_btn_edit_question_backend);
            jQuery(academy_test_question).find('.btn-edit-question-discard').on("click", obj.on_btn_edit_question_discard);
            jQuery(academy_test_question).find('.btn-edit-question-save').on("click", obj.on_btn_edit_question_save);
            jQuery(academy_test_question).find('.btn-edit-question-close').on("click", obj.on_btn_edit_question_discard);

        },

        requery : function (question_id, mode) {

            values = {'question_id': question_id, mode};

            ready = session.rpc("/ajax/get-question", values).then(function (result) {

                    /* STEP 2: Get question LI DOM item */
                    academy_test_question = jQuery('#academy-test-question-' + question_id);

                    /* STEP 3: Get parent */
                    swap_area = jQuery(academy_test_question);
                    json = JSON.parse(result);
                    jQuery(swap_area).html(json['html']);

                    /* STEP 4: bind events of the new items */
                    obj.bind_events(academy_test_question);

            });
        },



        /** Button events
        ---------------------------------------------------------------------*/

        on_btn_edit_question_click : function(e) {
            self = this;

            /* STEP 1: Get ID stored in a button DATA attribute  */
            question_id = jQuery(self).data('question-id');

            obj.requery(question_id, 'edit');
        },

        on_btn_revise_question_click : function(e) {
            self = this;

            clicks++;  //count clicks

            if(clicks === 1) {

                timer = setTimeout(function() {

                    /* STEP 1: Get ID stored in a button DATA attribute  */
                    question_id = jQuery(self).data('question-id');

                    /* STEP 2: Get question LI DOM item */
                    academy_test_question = jQuery('#academy-test-question-' + question_id);

                    /* STEP 3: Toggle visibility */
                    chksel = '.academy-test-answer-iscorrect-checkmark';
                    jQuery(academy_test_question).find(chksel).toggle();

                    clicks = 0;             //after action performed, reset counter

                }, DELAY);

            } else {

                clearTimeout(timer);    //prevent single-click action

                /* STEP 1: Get ID stored in a button DATA attribute  */
                id = jQuery(self).data('question-id');

                /* STEP 2: Get question LI DOM item */
                academy_test_question = jQuery('#academy-test-question-' + id);

                /* STEP 3: Check if some answer has the check mark visible */
                chksel = '.academy-test-answer-iscorrect-checkmark:visible';
                is_checked = jQuery(academy_test_question).find(chksel).length > 0;

                /* STEP 4: Change visibility of all check marks in oposite to the
                selected question */
                question_ids = jQuery('.academy-test-question-ids')

                if (is_checked == true) {
                    visible = jQuery(question_ids).find('.academy-test-answer-iscorrect-checkmark').hide();
                } else {
                    visible = jQuery(question_ids).find('.academy-test-answer-iscorrect-checkmark').show();
                }

                clicks = 0;             //after action performed, reset counter

            }
        },

        on_btn_revise_question_dblclick : function(e) {
             e.preventDefault();  //cancel system double-click event
        },

        on_ir_attachment_image_datas : function(e) {

            modal = jQuery('#academy-post-test-image-zoom')
            span = modal.find('span.academy-test-question-ir-attachment-image')
            img = modal.find('img.academy-test-question-ir-attachment-image')

            src = jQuery(this).attr('href');
            title = jQuery(this).attr('title');

            span.text(title);
            img.attr('src', src);
            img.attr('alt', title);
            img.attr('title', title);

            modal.modal('show');

            e.preventDefault();  //cancel system double-click event
        },

        on_btn_edit_question_backend : function(e) {

            /* STEP 1: Get ID stored in a button DATA attribute  */
            question_id = jQuery(self).data('question-id');

            /* STEP 2: Get question LI DOM item */
            academy_test_question = jQuery('#academy-test-question-' + question_id);

            /* new Model('ir.model.data').call('get_object_reference',
            ['academy_tests', 'action_questions_act_window']) */

            rpc.query({
                model: 'ir.model.data',
                method: 'get_object_reference',
                args: ['academy_tests', 'action_questions_act_window']
            }).then(function(action_id) {
                action_id = action_id[1];

                /** --- THIS MUST BE CHANGED ---**/
                //url = '/web#id=' + question_id + '&view_type=form&model=academy.tests.question&menu_id=128&action=' + action_id;
                url = '/web#id=' + question_id + '&model=academy.tests.question&menu_id=128&action=' + action_id;
                window.open(url, 'backend').focus();

                obj.requery(question_id, 'show');

            });
        },

        on_btn_edit_question_discard : function(e) {

            self = this;

            /* STEP 1: Get ID stored in a button DATA attribute  */
            question_id = jQuery(self).data('question-id');

            obj.requery(question_id, 'show');
        },

        on_btn_edit_question_save : function(e) {

            /* STEP 1: Get ID stored in a button DATA attribute  */
            question_id = jQuery(this).data('question-id');

            /* STEP 2: Get question LI DOM item */
            academy_test_question = jQuery('#academy-test-question-' + question_id);

            values = obj.get_data(academy_test_question, question_id);

            delete values['question_id'];

            /* --- PERHAPS THIS SHOULD BE TROUGHT THE CONTROLLER ---
            new Model('academy.tests.question').call('write', [[question_id], values])*/
            rpc.query({
                model: 'academy.tests.question',
                method: 'write',
                args: [[question_id], values]
            }).done(function(result) {
                console.log(result);
            }).always(function(result) {
                if (result != true) {
                    window.alert(JSON.stringify(result));
                } else {
                    obj.requery(question_id, 'show');
                };

            });
        },

        get_data : function (li_obj, question_id) {
            var values = {
                'question_id': question_id,
                'name': li_obj.find('.academy-test-question-name').val(),
                'preamble': li_obj.find(".academy-test-question-preamble").val(),
                'description': li_obj.find('.academy-test-question-description').val(),
                'answer_ids': []
            }

            li_obj.find('.academy-test-answer').each(function(i){
                id = $(this).data('id');
                name = $(this).find('.academy-test-answer-name').val();
                checked = $(this).find('input[type=checkbox]').prop('checked');
                values['answer_ids'].push([1, id, {'name': name, 'is_correct': checked }]);
            });

            return values;
        }
    });


    /*-- Impugment modals
    ------------------------------------------------------------------------*/

    $('#academy-post-test-inpugnment-modal').on('show.bs.modal', function (e) {
        self = this;

        question_id = jQuery(e.relatedTarget).data('question-id');

        /*-- STEP 1: Change modal title --*/
        atqid_span = 'span.academy-test-question-inpugment-academy-test-question-id'
        jQuery(self).find(atqid_span).text(question_id);

        /*-- STEP 2: Set token and question_id --*/
        token = 'input[name="csrf_token"]'
        csrf_token = $("#csrf_token").val()

        jQuery(self).find(token).val(csrf_token);

        atqid = 'input[name="academy-test-question-inpugment-academy-test-question-id"]';
        jQuery(self).find(atqid).val(question_id);

        /*-- STEP 3:  Clear fields --*/
        name = 'input[name="academy-test-question-inpugment-name"]';
        jQuery(self).find(name).val('');

        desc = 'textarea[name="academy-test-question-inpugment-description"]';
        jQuery(self).find(desc).val('');

        /*-- STEP 4: Diseble send button --*/
        $('#academy-post-test-inpugnment-modal .academy-test-question-send').prop('disabled', true);
    })


    jQuery('#academy-post-test-inpugnment-modal .academy-test-question-send').click(function() {

        atqid = 'input[name="academy-test-question-inpugment-academy-test-question-id"]';
        name = 'input[name="academy-test-question-inpugment-name"]';
        desc = 'textarea[name="academy-test-question-inpugment-description"]';

        values = {
            'question_id' : jQuery(atqid).val(),
            'name' : jQuery(name).val(),
            'description' : jQuery(desc).val(),
        };

        try {
            //new Model("academy.tests.question.impugnment").call("create", [values])

            rpc.query({
                model: 'academy.tests.question.impugnment',
                method: 'create',
                args: [values]
            }).then(function (result) {

                    jQuery('#academy-post-test-inpugnment-modal').modal('hide');

                    resm = jQuery('#impugnment-result-modal');
                    msgp = jQuery(resm).find('.impugnment-result-message');

                    jQuery('.impugnment-result-modal-academy-test-question-inpugment-id').text(result);
                    jQuery('.impugnment-result-modal-academy-test-question-id').text(values['question_id']);
                    jQuery('.impugnment-result-modal-name').text(values['name']);
                    jQuery('.impugnment-result-modal-description').text(values['description']);

                    jQuery('#impugnment-result-modal').modal('show');

                    $(resm).modal('show');
                });
        }
        catch(err) {
            alert(err);
        }

    });

    /* Inpugnment modal disable send
    -------------------------------------------------------------------------*/

    $('#academy-post-test-inpugnment-modal .academy-test-question-inpugment-name').on('input', function() {
        len = jQuery(this).val().length
        $('#academy-post-test-inpugnment-modal .academy-test-question-send').prop('disabled', len <= 0);
    });

    jQuery('.academy-test-question').each(function(i, val){new AtQuestion(val); })
});

