odoo.define('website_portal', function(require) {
    'use strict';
    var ajax = require('web.ajax');
    var Dialog = require('web.Dialog');
    //require('web');
    require('web.dom_ready');

    /**
     * Retrieves the page dependencies for the given object id.
     *
     * @private
     * @param {integer} moID
     * @param {Object} context
     * @returns {Deferred<Array>}
     */

    function savesheet() {
         console.log("in save")
         var values = [];
         var error = false
         $('.o_website_portal_details .required input').each(function (value) {
             if ($(this).val() == '')
                 error = true
                 $("#errortext").show()
         });
         $('.invalid').each(function (value){
             error = true
             $("#errortext-hours").show()
         })
         if (!error) {
             $('.o_website_portal_details input, .o_website_portal_details textarea').each(function (value) {
                 // values[$(this).attr(name)] = $(this).val()
                 values.push({"field": $(this).attr("name"), "value": $(this).val()});
             });
             ajax.jsonRpc("/my/update_timesheet/" + $("#savesheet").attr('sheetid'), 'call', {'values': values}).then(function (data) {
                 if (data.error) {
                     alert("test1")
                     self.display_alert(data.error);
                     self.$('.oe_slides_upload_loading').hide();
                     self.$('.modal-footer, .modal-body').show();

                 } else {
                      setTimeout(function () {
                        window.location = "/my/timesheet/" + $("#confirmsheet").attr('sheetid');
                    }, 1000);
                 }
             });
             return true
         }
         else
         {
             return false
         }
    }

    $("#reference_date").on("change", function () {
        var vars = {};
        vars.ref_date = $("#reference_date").val();
        ajax.jsonRpc("/my/update_holiday_stats", 'call', {'values': vars}).then(function (data) {
            for (var val in data.holiday_values) {
                $("#" + val).html(data.holiday_values[val].toFixed(1).replace(/\.?0*$/,''))
            }
        });
    });

    $("#savesheet").on("click", function () {

        savesheet()
     });



    $("#confirmsheet").on("click", function () {
        var values = [];
        var def = $.Deferred();
        var hour_mismatch = false
        var vars = {};
        $('.o_website_portal_details input').each(function (value) {
                 // values[$(this).attr(name)] = $(this).val()
                 values.push({"field": $(this).attr("name"), "value": $(this).val()});
             }).promise().done(function () {
        ajax.jsonRpc("/my/get_hours/" + $("#savesheet").attr('sheetid'), 'call', {'values': values}).then(function (data) {
            console.log(data)
            if (data != true){
                var confirmDef = $.Deferred();
                var message =  "The number of hours you entered doesn't match the hours defined in your contract. You need to enter " + data.contract + " hours based on your contract but you entered " + data.total + ". Are you sure you want to confirm these hours?";
                Dialog.confirm(self, message, {
                    title: "Hours mismatch!",
                    confirm_callback: confirmDef.resolve.bind(confirmDef),
                    cancel_callback: def.resolve.bind(self),
                });
//                Dialog.safeConfirm(self, "bla", {
//                    title: "Hours mismatch!",
//                    $content: "The number of hours you entered doesn't match the hours defined in your contract.You need to enter <span style='color:red'>" + data.contract + "</span> hours based on your contract but you entered <span style='color:red'>" + data.total + "</span>",
//                    confirm_callback: confirmDef.resolve.bind(confirmDef),
//                    cancel_callback: def.resolve.bind(self),
//                });
                hour_mismatch = true
                vars.contract_hours = data.contract;
                vars.form_hours = data.total;
                return confirmDef;
            }
            else
                return true
        }).then(function () {
            if (savesheet()) {
                // $('.o_website_portal_details input').each(function (value) {
                //     // values[$(this).attr(name)] = $(this).val()
                //     values.push({"field": $(this).attr("name"), "value": $(this).val()});
                //
                // });
                vars.hour_mismatch = hour_mismatch;
                ajax.jsonRpc("/my/confirm_timesheet/" + $("#savesheet").attr('sheetid'), 'call', {'vars': vars}).then(function (data) {
                    if (data.error) {
                        self.display_alert(data.error);
                        self.$('.oe_slides_upload_loading').hide();
                        self.$('.modal-footer, .modal-body').show();

                    } else {
                        setTimeout(function () {
                            window.location = "/my/timesheet/" + $("#confirmsheet").attr('sheetid');
                        }, 1000);
                    }
                });
                // console.log(values)
                // console.log($(this).attr('sheetid'))
            }
        })
     });
    });


    // $("#approvesheet").on("click", function () {
    //      var values = [];
    //      ajax.jsonRpc("/timesheet/approve/" + $(this).attr('sheetid') + "/" +$(this).attr('token'), 'call', {'values':values}).then(function (data) {
    //             if (data.error) {
    //                 alert("test1")
    //                 self.display_alert(data.error);
    //                 self.$('.oe_slides_upload_loading').hide();
    //                 self.$('.modal-footer, .modal-body').show();
    //             } else {
    //                 window.location = "/timesheet/" + $("#approvesheet").attr('sheetid') + "/" + $("#approvesheet").attr('token');
    //             }
    //         });
    //  });

    $(".tasktab").on("click", function () {

         var taskid

         $(".tasktab").removeClass("activetasktab")
         $(this).addClass("activetasktab")
         taskid = $(this).attr("id").split("_")[1]
         $(".task").removeClass("activetask")
         $("#task_"+taskid).addClass("activetask")
         $(".task_block").hide()
         $(".task_total").hide()
         $("[id^='task_block_"+taskid+"']").show()
         $("[id^='task_total_"+taskid+"']").show()
     });

    $(".values input").on("change", function () {
        var total = 0
        var hourtype = $(this).attr("name").split("_")[0]
        var taskid = $(this).attr("name").split("_")[1]
        $('.values input[name^=' + hourtype + '_' + taskid +']').each(function (value) {
            total += Number($(this).val().replace(",", "."))
        });
        $('input[name^=' + hourtype + '_' + taskid +'_total]').val(total)
        if(hourtype != "fromtime" || hourtype != "totime")
        {
            if($(this).val() < 0 || $(this).val() > 24 || $(this).val().search(/(\.|,)[0-9]{3}/) > 0)
            {
                $(this).addClass("invalid")
            }
            else
            {
                $(this).removeClass("invalid")
            }
        }
        if($(this).val() == "")
            $(this).val(0)
        if ($(this).parent().parent().hasClass("overtime"))
        {
            if ($(this).val() != 0)
                $(this).parent().parent().find('input').each(function (value) {
                    $(this).parent().addClass("required")
                });
            else
                $(this).parent().parent().find('input').each(function (value) {
                    $(this).parent().removeClass("required")
                });
        }
    });

    function calculate_totals()
    {
        $('.tasktab').each(function (value) {
            var total = 0
            var taskid = $(this).attr("id").split("_")[1]
            $('.values input[name^=regular_' + taskid +']').each(function (value) {
                total += Number($(this).val().replace(",","."))
            });
            $('input[name^=regular_' + taskid +'_total]').val(total)
        });

        $.each(['vacation','adv','illness','nw'], function( index, value ) {
            var total = 0
            $('.values input[name^=' + value + '_other]').each(function (val) {
                total += Number($(this).val().replace(",","."))
            });
            $('input[name=' + value + '_other_total]').val(total)
        });

    }

    function iphone()
    {
        console.log('user agent: ' + window.navigator.userAgent);

        if (window.navigator.userAgent.indexOf('iPhone') != -1) {
            $('.el-line-height').addClass('el-line-height-iphone').removeClass('el-line-height');
            $('.el-height').addClass('el-height-iphone').removeClass('el-height');
            $('.other-hours-heading').addClass('other-hours-heading-iphone').removeClass('other-hours-heading');
        }
    }

    $( document ).ready(function() {
        $(".task_block").hide()
        $(".task_total").hide()
        $(".ro input").css('background','gainsboro')
        $(".ro input").prop('readonly','readonly')
        //$(".ro input[required]").removeAttr('required')​​​​​
        $(".tasktab").first().click();
        $('input[type="time"]').each(function (value) {
            $(this).val($(this).attr('timevalue'))
        });
        $(".ro .required").removeClass('required')
        $(".holiday .required").removeClass('required')
        $("input[required]").parent().after().attr("style","")
        iphone();
        calculate_totals()
    });
});
