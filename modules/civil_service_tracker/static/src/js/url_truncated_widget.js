odoo.define('civil_service_tracker.url_truncated_widget', function (require) {
    'use strict';

    const field_registry = require('web.field_registry');
    const AbstractField = require('web.AbstractField');

    const UrlTruncatedWidget = AbstractField.extend({
        className: 'o_field_url_truncated',
        supportedFieldTypes: ['char'],
        tagName: 'a',
        attributes: {
            target: '_blank',
            rel: 'noopener noreferrer',
        },

        _renderReadonly: function () {
            const url = this.value;
            if (!url) {
                this.$el.text('');
                return;
            }

            this.$el.attr('href', url);
            this.$el.html(`<span class="o_url_text">${_.escape(url)}</span>`);
            this.$el.css({
                'max-width': '300px',
                'display': 'inline-block',
                'overflow': 'hidden',
                'white-space': 'nowrap',
                'text-overflow': 'ellipsis',
                'vertical-align': 'middle',
            });
        },
    });

    field_registry.add('url_truncated', UrlTruncatedWidget);
});
