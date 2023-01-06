odoo.define("dws_mail_messages.list_controller", function(require) {
    "use strict";

    var ListController = require("web.ListController");

    ListController.include({
        _getPagingInfo: function (state) {
            if (!state.count) {
                return null;
            }
            var pager = this._super(...arguments);
            if (state.model === "mail.message" || this.modelName === "mail.message") {
                pager.editable = false;
            }
            return pager;
        },
    });

    return ListController;
});
