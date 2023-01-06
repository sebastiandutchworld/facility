odoo.define('dws_dae_recruitment.portal_resume_line', function (require) {
'use strict';

var publicWidget = require('web.public.widget');
var time = require('web.time');
var rpc = require('web.rpc');

$(document).ready(function () {
         $(".modal_new_line").on('show.bs.modal', function (e) {
         $(".modal_new_line .line_type_id").val($(e.relatedTarget).attr('default-linetype-id'))
         $(".modal_new_line .line_type_id").change()
     });
 });

publicWidget.registry.EmpPortalResume = publicWidget.Widget.extend({
    selector: '#wrapwrap:has(.new_line_form, .edit_skill_form, #sendinbutton)',
    events: {
        'click .new_line_confirm': '_onNewLineConfirm',
        'click .edit_skill_line_confirm': '_onEditSkillConfirm',
        'click button.remove_resume_line': '_onButtonClickRemoveResumeLine',
        'change .new_line_form select[name="line_type_id"]':'_onlineTypeChange',
        'change .edit_skill_form select[name="line_type_id"]':'_onlineTypeChange',
        'click button.resume_send_in': '_onSendInButtonClick',
        'click button.resume_submit': '_onSubmitButtonClick',
    },

    _buttonExec: function ($btn, callback) {
        $btn.prop('disabled', true);
        return callback.call(this).guardedCatch(function () {
            $btn.prop('disabled', false);
        });
    },
    _onSendInButtonClick: function (ev) {
    	var lineId = $(ev.currentTarget).data('id'); //parseInt($('.skill_lines').data('id'));
        if (confirm("Your resume will be send in, do you want to continue?")) {
            return this._rpc({
                model: 'hr.resume.line',
                method: 'check_completeness',
                args: [{
                    employee_id: $('.new_line_form .emp_id').val(),
                }],
            }).then(function (response) {
                console.log(response)
                if (response == "False"){
                    alert("Your Resume is not complete\n" +
                        "You must fill in at least Work Experience and Education\n")
                }
                else {
                    window.location.reload();
                    alert("You sent your CV. Thank you!")
                }
            });
        }
    },
    _onSubmitButtonClick: function (ev) {
                    alert("Your Resume is saved\n" +
                        "You can safely leave this page now\n")
    },
    _createLine: function () {
    	return this._rpc({
            model: 'hr.resume.line',
            method: 'create_resume_line',
            args: [{
                name: $('.new_line_form .name').val(),
                line_type_id: $('.new_line_form .line_type_id').val(),
                date_start: $('.new_line_form .date_start').val(),
                date_end: $('.new_line_form .date_end').val(),
                graduated_on_date: $('.new_line_form .graduated_on_date').val(),
                description: $('.new_line_form .description').val(),
                employee_id: $('.new_line_form .emp_id').val(),
                aircraft_type: $('.new_line_form .aircraft_type').val(),
                company: $('.new_line_form .company').val(),
            }],
        }).then(function (response) {
            if (response.errors) {
                $('#new-opp-dialog .alert').remove();
                $('#new-opp-dialog div:first').prepend('<div class="alert alert-danger">' + response.errors + '</div>');
                return Promise.reject(response);
            } else {
                //window.location = '/my/resume_line/' + response.id;
                window.location = '/my/skills';
            }
        });
    },
    _editSkillRequest: function () {
        return this._rpc({
            model: 'hr.resume.line',
            method: 'update_resume_portal',
            args: [{
            	skillID: parseInt($('.edit_skill_form .skill_id').val()),
            	name: $('.edit_skill_form .name').val(),
            	description: $('.edit_skill_form .description').val(),
                line_type: $('.edit_skill_form .line_type_id').val(),
                date_start: this.$('.edit_skill_form .date_start').val(),
                date_end: this.$('.edit_skill_form .date_end').val(),
                aircraft_type: $('.edit_skill_form .aircraft_type').val(),
                company: $('.edit_skill_form .company').val(),
                graduated_on_date: $('.edit_skill_form .graduated_on_date').val()
            }],
        }).then(function (response) {
            if (response.errors) {
                $('#sign-dialog .alert').remove();
                $('#sign-dialog div:first').prepend('<div class="alert alert-danger">' + response.errors + '</div>');
                return Promise.reject(response);
            } else {
                //window.location = '/my/resume_line/' + response.id;
                window.location.reload();
            }
        });
    },
    _onButtonClickRemoveResumeLine: function (ev) {
    	var lineId = $(ev.currentTarget).data('id');
    	if (confirm("Are you sure you want to delete this row?")) {
            return this._rpc({
                model: 'hr.resume.line',
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
    _parse_date: function (value) {
        console.log(value);
        var date = moment(value, "YYYY-MM-DD", true);
        if (date.isValid()) {
            return time.date_to_str(date.toDate());
        }
        else {
            return false;
        }
    },
    _onlineTypeChange:function(ev) {
        console.log($(ev.currentTarget).val())
        if ($(ev.currentTarget).val() != '') {
            $('.new_line_form #additional_fields, .edit_skill_form #additional_fields_edit').addClass("d-none");
            $('.new_line_form #additional_fields input, .edit_skill_form #additional_fields_edit input').each(function () {
                $(this).val('');
            });
            $(".new_line_form label[for='date_start'], .edit_skill_form label[for='date_start']").parent().show();
            $(".new_line_form label[for='date_end'], .edit_skill_form label[for='date_end']").parent().show();
            $(".new_line_form label[for='graduated_on_date'], .edit_skill_form label[for='graduated_on_date']").parent().hide();
            $(".new_line_form label[for='name'], .edit_skill_form label[for='name']").html("Name");
            $(".new_line_form input[name='name'], .edit_skill_form input[name='name']").attr("placeholder", "");
            $(".new_line_form textarea[name='description'], .edit_skill_form textarea[name='description']").attr("placeholder", "");
            var args = [
                [['id', '=', $(ev.currentTarget).val()]],
                ['display_type'],
            ];
            rpc.query({
                model: 'hr.resume.line.type',
                method: 'search_read',
                args: args,
            }).then(function (data) {
                switch (data[0].display_type) {
                    case "experience":
                        $(".new_line_form label[for='name'], .edit_skill_form label[for='name']").html("Job title");
                        $('.new_line_form #additional_fields, .edit_skill_form #additional_fields_edit').removeClass("d-none");
                        $(".new_line_form textarea[name='description'], .edit_skill_form textarea[name='description']").attr("placeholder", "responsibilities,task and authorizations");
                        $(".new_line_form label[for='date_start'], .edit_skill_form label[for='date_start']").html("From");
                        $(".new_line_form label[for='date_end'], .edit_skill_form label[for='date_end']").html("To");
                        break;
                    case "cert":
                        $(".new_line_form label[for='name'], .edit_skill_form label[for='name']").html("Certificate");
                        $(".new_line_form label[for='date_start'], .edit_skill_form label[for='date_start']").html("Achieved Date");
                        $(".new_line_form label[for='date_end'], .edit_skill_form label[for='date_end']").html("Valid Until");
                        break;
                    case "study":
                        //$(".new_line_form label[for='date_start'], .edit_skill_form label[for='date_start']").parent().hide();
                        $(".new_line_form label[for='graduated_on_date'], .edit_skill_form label[for='graduated']").parent().show();
                        $(".new_line_form label[for='date_start'], .edit_skill_form label[for='date_start']").html("From");
                        $(".new_line_form label[for='date_end'], .edit_skill_form label[for='date_end']").html("To");
                        break;
                    case "language":
                        $(".new_line_form label[for='name'], .edit_skill_form label[for='name']").parent().hide();
                        $(".new_line_form input[name='name'], .edit_skill_form input[name='name']").val("Level english");
                        $(".new_line_form textarea[name='description'], .edit_skill_form textarea[name='description']").attr("placeholder", "Basic user/ Independent user / Proficient user");
                        $(".new_line_form label[for='date_start'], .edit_skill_form label[for='date_start']").parent().hide();
                        $(".new_line_form label[for='date_end'], .edit_skill_form label[for='date_end']").parent().hide();
                        break;
                    default:
                        $(".new_line_form label[for='date_start'], .edit_skill_form label[for='date_start']").html("From");
                        $(".new_line_form label[for='date_end'] .edit_skill_form label[for='date_end']").html("To");
                }
            });
        }
    }
});
});
