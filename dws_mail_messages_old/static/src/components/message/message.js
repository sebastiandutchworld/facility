odoo.define('dws_mail_messages/static/src/components/message/message.js', function (require) {
'use strict';

    const components = {Message: require('mail/static/src/components/message/message.js')};
    const { patch } = require('web.utils');

    patch(components.Message, 'dws_mail_messages/static/src/components/message/message.js', {
        /**
         * @private
         * @param {MouseEvent} ev
         */
        _onMessageReply(ev) {
            ev.stopPropagation();
            this.message.replyMessage();
        },
    });

});
