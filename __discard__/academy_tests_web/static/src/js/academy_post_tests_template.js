odoo.define('academy_tests_web.service', function (require) {
    "use strict";


    var core = require('web.core');
    var rpc = require('web.rpc');


    var PostTestsPage = core.Class.extend({

        css : [
            'academy_post_tests_template'
        ],


        events: {
            // 'click a[data-download-pdf]' : '_onDownloadPDF',
            'show.bs.dropdown .table-responsive' : '_onShowDropdown',
            'hide.bs.dropdown .table-responsive' : '_onHideDropdown'
        },


        init: function () {
            var self = this;

            if (self._get_container()) {
                self._link_stylesheets();
                self._bind_events();
            }
        },


        /**
         * Gets bootstrap page container will be used as DOM root.
         *
         * @private
         * @returns {boolean} true if element was found, false otherwise
         */
        _get_container : function () {
            var self = this;

            self.$dom = $('#academy_post_tests');

            return self.$dom.size() === 1;
        },


        /**
         * Links stylesheet files given in self.css attribute. This files
         * must be inside {module}/static/src/css/ and have .css extension.
         *
         * @private
         */
        _link_stylesheets : function () {
            var self = this;
            var i;

            var path = '/academy_tests_web/static/src/css/{file}.css';
            var link = '<link rel="stylesheet" type="text/css" href="{path}">';

            for (i = 0; i < self.css.length; i++) {
                $('head').append(
                    link.replace('{path}', path.replace('{file}', self.css[i]))
                );
            }
        },


        /**
         * Parse this.events dictionary binding the events
         *
         * @private
         */
        _bind_events : function () {
            var self = this;
            var item, space, event, selector, handler;

            for(item in self.events) {
                space = item.indexOf(' ');

                event = item.substring(0, space);
                selector = item.substring(space + 1, item.length);
                handler = self.events[item]

                self.$dom.find(selector).on(event, self[handler]);
            }
        },


        /**
         * Click event handler for PDF download buttons
         *
         * @private
         * @param {MouseClick} event
         */
        _onDownloadPDF : function (event) {
            var test_id = $(this).data('downloadPdf');

        },

        _onShowDropdown : function (event) {
            $('.table-responsive').css( "overflow", "inherit" );
        },

        _onHideDropdown : function (event) {
            $('.table-responsive').css( "overflow", "auto" );
        }

    });

    new PostTestsPage();

});
