odoo.define('civil_service_tracker.quick_offer_form_patch', function (require) {
    "use strict";

    const FormController = require('web.FormController');

    FormController.include({
        on_attach_callback() {
            this._super(...arguments);

            if (this.modelName === 'civil.service.tracker.quick.offer.wizard') {
                const $dialog = this.$el.closest('.modal');
                $dialog.addClass('quick-offer-modal');
            }
        },
    });
});
