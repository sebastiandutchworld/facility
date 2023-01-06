odoo.define('dws_dae_recruitment.portal_skill_line', function (require) {
'use strict';

var publicWidget = require('web.public.widget');
var time = require('web.time');

publicWidget.registry.EmpPortalSkill = publicWidget.Widget.extend({
    selector: '#wrapwrap:has(.new_skill_line_form, .edit_skill_line_form, #sendinbutton)',
    events: {
        'click .new_skill_line_confirm': '_onNewLineConfirm',
        'click .edit_skill_line_confirm': '_onEditSkillConfirm',
        'click button.remove_skill_line': '_onDeleteSkillLineButtonClick',
    },
    _buttonExec: function ($btn, callback) {
        $btn.prop('disabled', true);
        return callback.call(this).guardedCatch(function () {
            $btn.prop('disabled', false);
        });
    },
    _createLine: function () {
    	return this._rpc({
            model: 'hr.resume.line',
            method: 'create_skill_line',
            args: [{
                skill_type_id: $('.new_skill_line_form .skill_type_id').val(),
                skill_id: $('.new_skill_line_form .skill_id').val(),
                skill_level_id: $('.new_skill_line_form .skill_level_ids').val(),
            	employee_id: $('.new_skill_line_form .emp_id').val(),
            }],
        }).then(function (response) {
            if (response.errors) {
                $('#new-skill-dialog .alert').remove();
                $('#new-skill-dialog div:first').prepend('<div class="alert alert-danger">' + response.errors + '</div>');
                return Promise.reject(response);
            } else {
                window.location = '/my/skill_line/' + response.id;
            }
        });
    },
    _editSkillRequest: function () {
        return this._rpc({
            model: 'hr.employee.skill',
            method: 'update_skill_portal',
            args: [[parseInt($('.edit_skill_line_form .skill_id').val())], {
            	skillID: parseInt($('.edit_skill_line_form .skill_id').val()),
            	skill_type_id: $('.edit_skill_line_form .skill_type_id').val(),
                skill_id: $('.edit_skill_line_form .skill_select_id').val(),
                skill_level_id: $('.edit_skill_line_form .skill_level_ids').val(),
            }],
        }).then(function () {
            window.location.reload();
        });
    },
    _onDeleteSkillLineButtonClick: function (ev) {
    	var lineId = $(ev.currentTarget).data('id'); //parseInt($('.skill_lines').data('id'));
        alert("test")
        if (confirm("Are you sure you want to delete this row?")) {
            console.log("test1")
            return this._rpc({
                model: 'hr.employee.skill',
                method: 'unlink',
                args: [lineId],
            }).then(function () {
                window.location.reload();
            });
        }
    },
    _onNewLineConfirm: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        this._buttonExec($(ev.currentTarget), this._createLine);
    },
    _onEditSkillConfirm: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        this._buttonExec($(ev.currentTarget), this._editSkillRequest);
    },
});
});
