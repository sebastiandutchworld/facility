odoo.define('dws_mail_messages/static/src/models/message/message.js', function (require) {
'use strict';

    const { _lt } = require('web.core');
    const { registerInstancePatchModel,} = require('mail/static/src/model/model_core.js');

    registerInstancePatchModel('mail.message', 'dws_mail_messages/static/src/models/message/message.js', {
        /**
         * Launch unlink rpc
         */
        replyMessage() {
//            console.log(this.env)
            this.env.bus.trigger('do-action', {
                action: {
                    name: 'dws_mail_messages.prt_mail_message_form',
                    views: [[false, 'form']],
                    view_type: 'form',
                    view_mode: 'form',
                    res_model: 'mail.message',
                    type: 'ir.actions.act_window',
                    target: 'current',
                    res_id: this.id,
                },
            });
//            this.do_action({
//                views: [[false, 'form']],
//                view_type: 'form',
//                view_mode: 'form',
//                res_model: 'mail.message',
//                type: 'ir.actions.act_window',
//                target: 'current',
//                res_id: [[this.id]],
//            });
        },
    });

});
        