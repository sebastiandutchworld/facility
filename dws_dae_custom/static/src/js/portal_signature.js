odoo.define('dws_dae_custom.signature_form', function (require){
    "use strict";

    //require('web_editor.ready');
    console.log("te")
    var ajax = require('web.ajax');
    //var base = require('web_editor.base');
    var core = require('web.core');
    var Widget = require("web.Widget");
    var rpc = require("web.rpc");

    var qweb = core.qweb;

    var SignatureForm = Widget.extend({
        template: 'dws_dae_custom.portal_signature',
        events: {
            'click #o_portal_sign_clear': 'clearSign',
            'click .o_portal_sign_submit': 'submitSign',
            'init #o_portal_sign_accept': 'initSign',
        },

        init: function(parent, options) {
            this._super.apply(this, arguments);
            this.options = _.extend(options || {}, {
                csrf_token: odoo.csrf_token,
            });
        },

        willStart: function() {
            return this._loadTemplates();
        },

        start: function() {
            this.initSign();
        },

        // Signature
        initSign: function () {
            console.log(this.options)
            this.$("#o_portal_signature").empty().jSignature({
                'decor-color': '#D1D0CE',
                'color': '#000',
                'background-color': '#fff',
                'height': '142px',
            });
            //this.empty_sign = this.$("#o_portal_signature").jSignature('getData', 'image');
            //this.$("#o_portal_signature").jSignature('setData', 'data:image/png;base64,' + this.options.signature);
        },

        clearSign: function () {
            this.$("#o_portal_signature").jSignature('reset');
        },

        submitSign: function (ev) {
            console.log(this.options)
            ev.preventDefault();

            // extract data
            var self = this;
            var $confirm_btn = self.$el.find('button[type="submit"]');

            // process : display errors, or submit
            var employee_id = self.$("#o_portal_employee_id").val();
            var reject_reason = self.$("#o_portal_reject_reason").val();
            var signature = self.$("#o_portal_signature").jSignature('getData', 'image');
            var is_empty = signature ? self.$("#o_portal_signature").jSignature('getData', 'native').length == 0 : true;

            this.$('#o_portal_employee_id').parent().toggleClass('has-error', !employee_id);
            this.$('#o_portal_reject_reason').parent().toggleClass('has-error', !reject_reason);
            this.$('#o_portal_sign_draw').toggleClass('panel-danger', is_empty).toggleClass('panel-default', !is_empty);
            if (((is_empty || ! employee_id) && this.options.actiontype == 'approval') || (!reject_reason && this.options.actiontype == 'rejection')) {
                return false;
            }

            $confirm_btn.prepend('<i class="fa fa-spinner fa-spin"></i> ');
            $confirm_btn.attr('disabled', true);

            if (this.options.actiontype == 'approval'){
                var params = {
                    'res_id': this.options.resId,
                    'access_token': this.options.accessToken,
                    'employee_id': employee_id,
                    'signature': signature ? signature[1] : false
                }
            }
            else {
                var params = {
                    'res_id': this.options.resId,
                    'access_token': this.options.accessToken,
                    'reject_reason': reject_reason,
                }
            }

            return rpc.query({
                route: this.options.callUrl,
                params: params,
            }).then(function (data) {
                self.$('.fa-spinner').remove();
                self.$('#o_portal_sign_accept').prepend('<div>PROUT' + data + '</div>');
                if (data.error) {
                    $confirm_btn.attr('disabled', false);
                }
                else if (data.success) {
                    $confirm_btn.remove();
                    var $success = qweb.render("daedalus_ems.portal_signature_success", {widget: data});
                    self.$('.form-group').parent().replaceWith($success);
                }
            });
        },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * @private
         * @returns {Deferred}
         */
        _loadTemplates: function () {
            return ajax.loadXML('/dws_dae_custom/static/src/xml/portal_signature.xml', qweb);
        },
    });

    //base.ready().then(function () {
    $(document).ready(function () {
        console.log('ready??');
        $('.o_portal_signature_form2').each(function () {
            var $elem = $(this);
            var form = new SignatureForm(null, $elem.data());
            form.appendTo($elem);
        });
    });

    return {
        SignatureForm: SignatureForm,
    };
});
