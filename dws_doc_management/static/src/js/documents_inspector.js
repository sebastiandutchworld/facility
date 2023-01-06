odoo.define("dws_doc_management.DocumentsInspector", function (require) {
    "use strict";

    const DocumentsInspector = require("documents.DocumentsInspector");

    DocumentsInspector.include({
    /**
     * @private
     * @return {Promise}
     */
    _renderFields: function () {
        const options = {mode: 'edit'};
        const proms = [];
        if (this.records.length === 1) {
            proms.push(this._renderField('name', options));
            if (this.records[0].data.type === 'url') {
                proms.push(this._renderField('url', options));
            }
            proms.push(this._renderField('valid_from', options));
            proms.push(this._renderField('valid_until', options));
            proms.push(this._renderField('signal_period_months', options));
            proms.push(this._renderField('partner_id', options));
        }
        if (this.records.length > 0) {
            proms.push(this._renderField('owner_id', options));
            proms.push(this._renderField('folder_id', {
                icon: 'fa fa-folder o_documents_folder_color',
                mode: 'edit',
            }));
        }
        return Promise.all(proms);
    },
    });
});
