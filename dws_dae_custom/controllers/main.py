# -*- coding: utf-8 -*-

import csv, sys
import base64
import logging
from odoo import exceptions, fields, http, _,SUPERUSER_ID
from odoo.http import request
from datetime import datetime, timedelta
#from odoo.addons.website_portal.controllers.main import website_account
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager

from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)
# class website_account(website_account):
class CustomerPortal(CustomerPortal):

    MANDATORY_BILLING_FIELDS = ["first_name", "surname", "phone", "email", "street", "city", "country_id"]
    OPTIONAL_BILLING_FIELDS = ["zipcode","surname_prefix", "state_id", "vat", "company_name"]

    def _prepare_portal_layout_values(self):
        print("test portal")
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        employee = request.env['hr.employee'].sudo().search(
            [('user_id.id', 'in', [request.env.user.id])], limit=1)
        print(employee)
        candidate = False
        if employee:
            applicant = request.env['hr.applicant'].sudo().search([('emp_id', '=', employee.id)], limit=1)
            if applicant.stage_id:
                candidate = True
        contract = request.env['hr.contract'].sudo().search(
            ['&',('employee_id', '=', employee.id),('state','=','open')], limit=1)
        holiday_values = employee.calc_vac_hours(datetime.now().strftime('%Y-%m-%d'))
        allowed_holidays = request.env['hr.leave.allocation'].sudo().search(
            [("employee_id","=",employee.id),("expiration_date", ">=", datetime.now().strftime('%Y-%m-%d')),
             ("expiration_date", "<", (datetime.today() + timedelta(2 * 365 / 12)).strftime('%Y-%m-%d')),
             ("allocation_date", "<=", datetime.now().strftime('%Y-%m-%d'))])
        expiring_holidays = []
        if allowed_holidays:
            for allowed_holiday in allowed_holidays:
                if ((allowed_holiday.holiday_status_id.type == '1' and (holiday_values['balance_ly'] - holiday_values['taken_cy']) > 0) or (allowed_holiday.holiday_status_id.type == '2' and holiday_values['balance_ly_adv'] > 0) or (allowed_holiday.holiday_status_id.type == '3' and holiday_values['balance_ly_all'] > 0)):
                    expiring_holidays.append({"type":dict(request.env['hr.leave.type']._fields['type'].selection)[str(allowed_holiday.holiday_status_id.type)],"expiration_date":allowed_holiday.expiration_date})

        timesheet_count = self._sheet_count()
        if timesheet_count > 13:
            timesheet_count = 13

        hide_adv = False
        hide_all = False

        if contract.above_legal_leave == 0:
            hide_all = True
        if contract.adv_leave == 0:
            hide_adv = True
        print(holiday_values)
        values.update({
            'banking_hours': employee.banking_hours,
            'holiday_hours': holiday_values,
            'timesheets_count': timesheet_count,
            'hide_adv': hide_adv,
            'hide_all': hide_all,
            'expiring_holidays':expiring_holidays,
            'reference_date': datetime.now().strftime('%Y-%m-%d'),
            'employee': employee,
            'candidate': candidate
        })
        return values

    # if actual number of timesheets is usefull, use this method for timesheets count
    def _sheet_count(self):
        sheets_data = request.env['employee.sheet'].sudo().read_group([('user_id', '!=', False)], ['user_id'],
                                                                      ['user_id'])
        result = dict((data['user_id'][0], data['user_id_count']) for data in sheets_data)
        return result.get(request.env.user.id, 0)

    @http.route(['/my/account'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        values.update({
            'error': {},
            'error_message': [],
        })

        if post and request.httprequest.method == 'POST':
            error, error_message = self.details_form_validate(post)
            values.update({'error': error, 'error_message': error_message})
            values.update(post)
            employee = values['employee']
            if not error:
                values = {key: post[key] for key in self.MANDATORY_BILLING_FIELDS}
                values.update({key: post[key] for key in self.OPTIONAL_BILLING_FIELDS if key in post})
                for field in set(['country_id', 'state_id']) & set(values.keys()):
                    try:
                        values[field] = int(values[field])
                    except:
                        values[field] = False
                values.update({'zip': values.pop('zipcode', '')})
                print(values)
                changes = ''
                for key,value in values.items():
                    if key == 'country_id':
                        if value != partner[key].id:
                            new_country = request.env['res.country'].sudo().search([('id', '=', value)], limit=1)
                            changes += '<p>' + str(key) + ' -> Old value: <strong>' + str(partner[key].name) + '</strong> - New value: <strong>' + str(new_country.name) + '</strong></p>'
                    else:
                        if value != partner[key]:
                            changes += '<p>' + str(key) + ' -> Old value: <strong>' + str(partner[key]) + '</strong> - New value: <strong>' + str(value) + '</strong></p>'
                partner.sudo().write(values)
                employee.name = partner.name
                activity_type = request.env['mail.activity.type'].sudo().search(
                    [('name', '=', 'Email')], limit=1
                )

                contact_change_activity = request.env['mail.activity.type'].sudo().search(
                    [('name', '=', 'Contact change')], limit=1
                )
                if not contact_change_activity:
                    contact_change_activity = request.env['mail.activity.type'].sudo().create({
                        'name': 'Contact change',
                        'res_model_id': request.env['ir.model']._get('res.partner').id,
                        'category': 'reminder',
                        'icon': 'fa-envelope',
                        'decoration_type': 'warning'
                    })

                if activity_type:

                    request.env['mail.activity'].sudo().create({
                        'res_model_id': request.env['ir.model']._get('res.partner').id,
                        'res_id': partner.id,
                        'user_id': 1,
                        'summary': 'Partner changed contact info',
                        'note': changes,
                        'activity_type_id': contact_change_activity.id,
                    })

                if redirect:
                    return request.redirect(redirect)
                return request.redirect('/my/home')

        countries = request.env['res.country'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])
        print(values)
        values.update({
            'partner': partner,
            'countries': countries,
            'states': states,
            'has_check_vat': hasattr(request.env['res.partner'], 'check_vat'),
            'redirect': redirect,
            'page_name': 'my_details',
        })

        response = request.render("portal.portal_my_details", values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @http.route("/timesheet/<int:sheet_id>/<token>", type='http', auth="public", website=True)
    def view(self, sheet_id, pdf=None, token=None, message=False, **post):
        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        print(token)
        hr_approval = False
        if token:
            approval = request.env['employee_sheet.approvals'].sudo().search([('sheet_id', '=', sheet_id), ('access_token', '=', token)])
            print(approval)

        if not approval:
             return request.render('website.404')

        timesheet = request.env['employee.sheet'].sudo().browse([sheet_id])
        if approval.partner_id.id == int(request.env['ir.config_parameter'].sudo().get_param('hr_approver_partner')):
            hr_approval = True
            task_search = request.env['project.task'].sudo().search([
                ('user_ids', 'in', [timesheet.user_id.id]),
                ('planned_date_begin', "<=", timesheet.enddate),
                ('planned_date_end', ">=", timesheet.startdate)])
        else:
            task_search = request.env['project.task'].sudo().search([
                ('user_ids', 'in', [timesheet.user_id.id]),
                ('planned_date_begin', "<=", timesheet.enddate),
                ('planned_date_end', ">=", timesheet.startdate),
                '|',
                ('customer_contact', '=', approval.partner_id.id),
                ('customer_contact2', '=', approval.partner_id.id),
                ('project_id', '=', approval.project_id.id)
        ])
        # task_search = request.env['project.task'].sudo().search([
        #     ('user_id','in',[timesheet.user_id.id]),
        #     ('date_start', "<=", timesheet.enddate),
        #     ('date_end', ">=", timesheet.startdate),('customer_contact', '=', approval.partner_id.id),('project_id','=',approval.project_id.id)
        # ])
        # #TO DO ... ugly solution here .... the search condition needs to be changed in the previous search instead!
        # if not task_search:
        #     task_search = request.env['project.task'].sudo().search([
        #     ('user_id','in',[timesheet.user_id.id]),
        #     ('date_start', "<=", timesheet.enddate),
        #     ('date_end', ">=", timesheet.startdate),('customer_contact2', '=', approval.partner_id.id),('project_id','=',approval.project_id.id)
        #     ])
        tasks = request.env['project.task'].sudo().browse(task_search)
        date1 = datetime.strptime(str(timesheet.startdate), "%Y-%m-%d")
        dates = [date1]
        i = 0
        while True:
            i = i + 1
            date2 = date1 + timedelta(days=1)
            print(date2.date())
            print(timesheet.enddate)
            if str(date2.date()) == str(timesheet.enddate) or i > 50:
                dates.append(date2)
                break
            else:
                dates.append(date2)
                date1 = date2
        print(dates)
        holidays = request.env['employee.sheet'].sudo().get_holidays()
        hours_search = request.env['employee.hours'].sudo().search([('employee_sheet_id', '=', timesheet.id)])
        employee_hours = []
        if hours_search:
            hours = request.env['employee.hours'].sudo().browse(hours_search)
            print(hours)
            for hour in hours:
                # print(hour.id.date)
                for type in ['fromtime', 'totime', 'regular', 'vacation', 'adv', 'illness','nw']:
                    if hour.id[type]:
                        if hour.id.task_id.id:
                            taskid = hour.id.task_id.id
                        else:
                            taskid = 'other'
                        employee_hours.append([type + '_' + str(taskid) + '_' + str(hour.id.date), hour.id[type]])
        else:
            hours = ''
        employee_hours = dict(employee_hours)
        print(employee_hours)
        # print(employee_hours['regular_28_2018-06-18'])
        # print(employee_hours['regular_28_2018-06-19'])
        print(approval.status)
        print(request.env['employee_sheet.approvals']._fields['status'].selection)
        if approval.status == False:
            approvalstatus = 0
        else:
            approvalstatus = approval.status

        values = {
            'sheet': timesheet,
            'tasks': tasks,
            'dates': dates,
            'holidays': holidays,
            'hours': employee_hours,
            'notes': timesheet['notes'],
            'status': timesheet['status'],
            'token': token,
            'approval_status': approvalstatus,
            'approval_status_text': dict(request.env['employee_sheet.approvals']._fields['status'].selection)[str(approvalstatus)],
            'approval': approval,
            'hr_approval': hr_approval
        }


        return request.render('dws_dae_custom.approve_timesheet', values)

    @http.route("/timesheet/approve", type='json', auth="none", website=True)
    def approve(self, res_id, access_token=None, employee_id=None, signature=None):
        print("teeest30")

        email_context = request.env.context.copy()

        if access_token:
            # approval = request.env['employee_sheet.approvals'].sudo().search(
            #     [('sheet_id', '=', sheet_id), ('access_token', '=', token)])

            approval = request.env['employee_sheet.approvals'].sudo().browse([res_id])
            #if we already have a signature saved then use it...otherwise use the one provided by the user by drawing on the canvas
            # if approval.partner_id.signature:
            #     sign = approval.partner_id.signature
            # else:
            #     sign = signature

            data = {'approver_id': approval.partner_id.id, 'sheet_id': approval.sheet_id.id, 'project_id': approval.project_id, 'imgbase64':signature,'employee_id':employee_id}
            pdf = request.env.ref('dws_dae_custom.custom_report_sheet').sudo()._render_qweb_pdf(False, data=data)[0]
            if approval.partner_id.id == int(request.env['ir.config_parameter'].sudo().get_param('hr_approver_partner')):
                approval.write(({'status': '1'}))
                approval.sheet_id.write(({'status': '2'}))
            else:
                approval.write(({'status': '1','pdf_report':base64.b64encode(pdf)}))
            #approval.partner_id.write({'signature': signature})
            #select other approval rows for the same project in the current sheet and mark them as approved also.
            sheet_approvals = request.env['employee_sheet.approvals'].sudo().search([('sheet_id', '=', approval.sheet_id.id),('project_id','=',approval.project_id.id),('id','!=',approval.id)])
            final_approved = True
            if sheet_approvals:
                for sheet_approval in sheet_approvals:
                    if approval.partner_id.parent_id == sheet_approval.partner_id.parent_id:
                        sheet_approval.write({'status': '1'})
            #         else:
            #             if sheet_approval.status != 1:
            #                 final_approved = False
            #
            # if final_approved == True:
            #     approval.sheet_id.write(({'status': '3'}))

            if approval.partner_id.id == int(request.env['ir.config_parameter'].sudo().get_param('hr_approver_partner')):
                contacts = approval.sheet_id.get_involved_contacts(approval.sheet_id.user_id.id)
                _logger.info(contacts)
                type = "main"
                for contact_type in contacts:
                    if contact_type:
                        for contact in contact_type:
                            approvals = request.env['employee_sheet.approvals'].sudo().search(
                                [('partner_id', '=', contact["contact"].id), ('sheet_id', '=', approval.sheet_id.id),
                                 ('project_id', '=', contact["project_id"])])
                            if approvals:
                                for approval in approvals:
                                    # reset the status of the rejected projects so they can approve or reject them again
                                    if approval.status == '2':
                                        approval.sudo().write(({'status': '0'}))


                            email_context.update({
                                'email_to': contact["contact"].email,
                                'token': approval.access_token,
                                'name': contact["contact"].name,
                                'employee_name': approval.sheet_id.user_id.partner_id.name,
                                'sheet_id': approval.sheet_id
                            })
                            if type == "main":
                                template = request.env.ref('dws_dae_custom.email_template_data_approval')
                            else:
                                template = request.env.ref('dws_dae_custom.email_template_data_approval2')
                            request.env['mail.template'].sudo().browse(template.id).with_context(email_context).send_mail(
                                approval.sheet_id.id)

                    type = "backup"

            approval.sheet_id.with_user(SUPERUSER_ID).verify_approval_status()

        return {
            'success': _('You succesfully validated the timesheet.'),
            'redirect_url': ''
        }

    @http.route("/timesheet/reject", type='json', auth="public", website=True)
    def reject(self, res_id, access_token=None, reject_reason=None):
        email_context = request.env.context.copy()
        if access_token:
            # approval = request.env['employee_sheet.approvals'].sudo().search(
            #     [('sheet_id', '=', sheet_id), ('access_token', '=', token)])

            approval = request.env['employee_sheet.approvals'].sudo().browse([res_id])

            approval.write(({'status': '2','notes': reject_reason}))
            approval.sheet_id.write(({'status': '0'}))
            # select other approval rows for the same project in the current sheet and mark them as rejected also.
            sheet_approvals = request.env['employee_sheet.approvals'].sudo().search(
                [('sheet_id', '=', approval.sheet_id.id),('project_id','=',approval.project_id.id),('id', '!=', approval.id)])
            if sheet_approvals:
                for sheet_approval in sheet_approvals:
                    if approval.partner_id.parent_id == sheet_approval.partner_id.parent_id:
                        sheet_approval.write({'status': '2'})

            email_context.update({
                'email_to': approval.sheet_id.user_id.partner_id.email,
                'token': approval.access_token,
                'name': approval.partner_id.name,
                'employee_name': approval.sheet_id.user_id.partner_id.name,
                'sheet_id': approval.sheet_id,
                'reject_reason': reject_reason
            })

        template = request.env.ref('dws_dae_custom.email_template_data_rejection')
        request.env['mail.template'].sudo().browse(template.id).with_context(email_context).send_mail(approval.sheet_id.id)

        return {
            'success': _('You succesfully rejected the timesheet.'),
            'redirect_url': ''
        }

    @http.route("/timesheet/downloadreport/<int:sheet_id>/<token>", type='http', csrf=False, auth="none",
                methods=['GET', 'POST'], website=True)
    def print_report_with_approver(self, sheet_id, token, **kw):
        print('download report action')
        approval = request.env['employee_sheet.approvals'].sudo().search(
            [('sheet_id', '=', sheet_id), ('access_token', '=', token)])
        approver_id = approval.partner_id.id
        project_id = approval.project_id

        sheet = request.env['employee.sheet'].sudo().search([('id', '=', sheet_id)])
        # pdf = request.env.ref('custom_daedalus_ems.custom_report_sheet').report_action([], config=False)
        data = {'approver_id': approver_id, 'sheet_id': sheet_id, 'project_id': project_id, 'imgbase64':'','employee_id':''}
        pdf = request.env.ref('dws_dae_custom.custom_report_sheet').sudo()._render_qweb_pdf(False, data=data)[0]
        # pdf = request.env.ref('custom_daedalus_ems.custom_report_sheet').sudo().render_qweb_html([14])[0]

        # request.env.ref('point_of_sale.sale_details_report').with_context(date_start=date_start,
        #                                                                   date_stop=date_stop).render_qweb_pdf(r)

        # pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf)),
        #                   ('Content-Disposition', 'attachment; filename=Report.pdf;')]
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf)),
                          ('Content-Disposition', 'attachment; filename=%s_%s_%s_approved.pdf;' % (
                          project_id.name.replace(" ", "_"), sheet.startdate, sheet.user_id.name.replace(" ", "_")))]
        return request.make_response(pdf, headers=pdfhttpheaders)

    @http.route("/timesheet/downloadreport/<int:sheet_id>", type='http', csrf=False, auth="user",
                methods=['GET', 'POST'], website=True)
    def print_report(self, sheet_id, **kw):
        print('download report action')
        #print(request.env.user.company_id.logo)
        sheet = request.env['employee.sheet'].sudo().search([('id', '=', sheet_id)])
        # pdf = request.env.ref('custom_daedalus_ems.custom_report_sheet').report_action([], config=False)
        # data = {'approver_id': '', 'sheet_id': sheet_id, 'project_id': '', 'imgbase64':'','employee_id':''}
        # pdf = request.env.ref('daedalus_ems.custom_report_sheet').sudo().render_qweb_pdf(False, data=data)[0]
        data = {'res_company': request.env.user.company_id[0]}
        pdf = request.env.ref('dws_dae_custom.custom_report_sheet_timesheets').with_user(SUPERUSER_ID)._render_qweb_pdf(sheet.id,data=data)[0]
        # pdf = request.env.ref('custom_daedalus_ems.custom_report_sheet').sudo().render_qweb_html([14])[0]

        # request.env.ref('point_of_sale.sale_details_report').with_context(date_start=date_start,
        #                                                                   date_stop=date_stop).render_qweb_pdf(r)

        # pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf)),
        #                   ('Content-Disposition', 'attachment; filename=Report.pdf;')]
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf)),
                          ('Content-Disposition', 'attachment; filename=%s_%s_approved.pdf;' % (
                          sheet.startdate, sheet.user_id.name.replace(" ", "_")))]
        return request.make_response(pdf, headers=pdfhttpheaders)

    @http.route("/timesheet/downloadapprovedreport/<int:sheet_id>/<token>", type='http', csrf=False, auth="public",
                methods=['GET', 'POST'], website=True)
    def download_approved_report(self, sheet_id, token, **kw):
        approval = request.env['employee_sheet.approvals'].sudo().search(
            [('sheet_id', '=', sheet_id), ('access_token', '=', token)])
        approver_id = approval.partner_id.id
        project_id = approval.project_id
        sheet = request.env['employee.sheet'].sudo().search([('id', '=', sheet_id)])
        # pdf = request.env.ref('custom_daedalus_ems.custom_report_sheet').report_action([], config=False)
        pdf = request.env['ir.attachment'].sudo().search([('res_model', '=', approval._name), ('res_id', '=', approval.id)])
        #print(pdf)

        # pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', base64.b64decode(approval.pdf_report)),
        #                   ('Content-Disposition', 'attachment; filename=Report.pdf;')]
        pdfhttpheaders = [('Content-Type', 'application/pdf'),
                          ('Content-Length', base64.b64decode(approval.pdf_report)),
                          ('Content-Disposition', 'attachment; filename=%s_%s_%s_approved.pdf;' % (
                          project_id.name.replace(" ", "_"), sheet.startdate, sheet.user_id.name.replace(" ", "_")))]
        return request.make_response(base64.b64decode(approval.pdf_report), headers=pdfhttpheaders)


    @http.route(['/my/timesheets', '/my/timesheets/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_timesheet(self, page=1, sortby=None, **kw):
        # if not request.env.user.has_group('odoo_timesheet_portal_user_employee.analytic_line_portal'):
        #     return request.render("odoo_timesheet_portal_user_employee.not_allowed")
        response = super(CustomerPortal, self)
        values = {}
        #values = self._prepare_portal_layout_values()
        timesheets_obj = request.env['employee.sheet']
        # only generate timesheets if user has employee set
        if request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1):
            timesheets_obj.sudo().generate_timesheets(request.env.user.id)
        currentsheet = timesheets_obj.sudo().search([('startdate',"<=",fields.Datetime.now()),('enddate',">=",fields.Datetime.now()),('user_id', 'in', [request.env.user.id])])
        #print(currentsheet)
        if currentsheet:
            date_overview = datetime.strptime(str(currentsheet[0].startdate), "%Y-%m-%d") - timedelta(weeks=(9 * 4))
            domain = [
                 ('user_id', 'in', [request.env.user.id]),('startdate','>',str(date_overview.date()))
             ]
            # count for pager
            #timesheets_count = http.request.env['account.analytic.line'].sudo().search_count(domain)
            #print(timesheets_count)
            # pager
            pager = request.website.pager(
                url="/my/timesheets",
                total=13,
                page=page,
                step=self._items_per_page
            )
            sortings = {
                'startdate': {'label': _('Newest'), 'order': 'startdate desc'}
            }

            order = sortings.get(sortby, sortings['startdate'])['order']

            # content according to pager and archive selected
            timesheets = timesheets_obj.sudo().search(domain, order='startdate asc', limit=13, offset=pager['offset'])
            #print(timesheets)
            #timesheets = timesheets_obj.sudo().get_timesheets(request.env.user.id)
            #timesheets = {}
            values.update({
                'timesheets': timesheets,
                'page_name': 'timesheets',
                'sortings' : sortings,
                'sortby': sortby,
                'pager': pager,
                'default_url': '/my/timesheets',
            })
            return request.render("dws_dae_custom.display_timesheets", values)


    @http.route(['/my/timesheet/<int:timesheet>'], type='http', auth="user", website=True)
    def edit_timesheet(self, timesheet=None, **kw):
        employee = request.env['hr.employee'].sudo().search(
            [('user_id.id', '=', [request.env.user.id])], limit=1)
        timesheet = request.env['employee.sheet'].sudo().browse([timesheet])
        task_search = request.env['project.task'].sudo().search([
             ('user_ids', 'in', [request.env.user.id]),('planned_date_begin',"<=",timesheet.enddate),('planned_date_end',">=",timesheet.startdate)
         ])
        _logger.info("User:" + str(request.env.user.id) + str(timesheet.enddate) + str(timesheet.startdate))
        tasks = request.env['project.task'].sudo().browse(task_search)
        date1 = datetime.strptime(str(timesheet.startdate), "%Y-%m-%d")
        dates = [date1]
        i = 0
        while True:
            i = i + 1
            date2 = date1 + timedelta(days=1)
            # print(date2.date())
            # print(timesheet.enddate)
            if str(date2.date()) == str(timesheet.enddate) or i > 50:
                dates.append(date2)
                break
            else:
                dates.append(date2)
                date1 = date2
        #print(dates)
        holidays = request.env['employee.sheet'].sudo().get_holidays()
        task_holidays = request.env['employee.sheet'].sudo().get_task_holidays(task_search)
        print(task_holidays)
        hours_search = request.env['employee.hours'].sudo().search([('employee_sheet_id','=',timesheet.id)])
        employee_hours = []
        if hours_search:
            hours = request.env['employee.hours'].sudo().browse(hours_search)
            #print(hours)
            for hour in hours:
                #print(hour.id.date)
                for type in ['fromtime','totime','regular','vacation','adv','illness','nw']:
                     if hour.id[type]:
                         if hour.id.task_id.id:
                             taskid = hour.id.task_id.id
                         else:
                             taskid = 'other'
                         employee_hours.append([type + '_' + str(taskid) + '_' + str(hour.id.date), hour.id[type]])
        else:
            hours = ''
        employee_hours = dict(employee_hours)
        #print(employee_hours)
        # print(employee_hours['regular_28_2018-06-18'])
        # print(employee_hours['regular_28_2018-06-19'])

        values={
            'sheet': timesheet,
            'tasks': tasks,
            'dates': dates,
            'holidays': holidays,
            'task_holidays': task_holidays,
            'hours': employee_hours,
            'notes': timesheet['notes'],
            'status': timesheet['status'],
            'employee': employee
        }
        
        return request.render("dws_dae_custom.edit_timesheet",values)

    @http.route(['/my/validate_timesheet/<int:timesheet>'], type='json', auth="user", methods=['POST'], website=True)
    def confirm_timesheet(self, timesheet, **kw):
        email_context = request.env.context.copy()
        sheet = request.env['employee.sheet'].sudo().browse(timesheet)

    @http.route(['/my/confirm_timesheet/<int:timesheet>'], type='json', auth="user", methods=['POST'], website=True)
    def confirm_timesheet(self, timesheet, **kw):

        email_context = request.env.context.copy()

        sheet = request.env['employee.sheet'].sudo().browse(timesheet)
        sheet.write({'status': '1'})

        print('vars=', request.params['vars'])

        if request.params['vars'].get('hour_mismatch') == True:
            email_context.update({
                'employee_name': sheet.user_id.partner_id.name,
                'sheet_id': sheet,
                'vars': request.params['vars']
            })
            template = request.env.ref('dws_dae_custom.email_template_data_hours_mismatch')
            request.env['mail.template'].sudo().browse(template.id).with_context(email_context).send_mail(sheet.id)

        #get the involved contacts
        vals = []

        #print("contacts")
        #print(contacts)
        #the first element of the array contains the main approvers and the second element the backup approvers
        #if we do not have any contacts for approving that means we have no tasks in the timesheet...let's transfer the other hours directly
        # if not contacts[0] and not contacts[1]:
        #     print("transfer hours")
        #     sheet.sudo().transfer_hours()
        type = "main"

        hr_contact = request.env['res.partner'].sudo().browse([int(request.env['ir.config_parameter'].sudo().get_param('hr_approver_partner'))])

        approvals = request.env['employee_sheet.approvals'].sudo().search([('partner_id', '=', hr_contact.id), ('sheet_id', '=', sheet.id)])

        if approvals:
            for approval in approvals:
                # reset the status of the rejected projects so they can approve or reject them again
                if approval.status == '2' or approval.status == '1':
                    approval.sudo().write(({'status': '0'}))
        else:
            approval = request.env['employee_sheet.approvals'].sudo().create(
                {'partner_id': hr_contact.id, 'sheet_id': sheet.id});

        email_context.update({
            'email_to': hr_contact.email,
            'token': approval.access_token,
            'name': hr_contact.name,
            'employee_name': sheet.user_id.partner_id.name,
            'sheet_id': sheet
        })
        print(email_context)
        template = request.env.ref('dws_dae_custom.email_template_data_approval')
        request.env['mail.template'].sudo().browse(template.id).with_context(email_context).send_mail(sheet.id)

        contacts = sheet.get_involved_contacts(request.env.uid)
        for contact_type in contacts:
            if contact_type:
                for contact in contact_type:
                    approvals = request.env['employee_sheet.approvals'].sudo().search(
                        [('partner_id', '=', contact["contact"].id), ('sheet_id', '=', sheet.id),
                         ('project_id', '=', contact["project_id"])])
                    if approvals:
                        for approval in approvals:
                            # reset the status of the rejected projects so they can approve or reject them again
                            if approval.status == '2':
                                approval.sudo().write(({'status': '0'}))
                    else:
                        approval = request.env['employee_sheet.approvals'].sudo().create(
                                    {'partner_id': contact["contact"].id, 'sheet_id': sheet.id,
                                     'project_id': contact["project_id"]});

        return True

    @http.route(['/my/update_timesheet/<int:timesheet>'], type='json', auth="user", methods=['POST'], website=True)
    def update_timesheet(self, timesheet,**kw):
        #print(timesheet)
        #print(request.params['values'])
        for field in request.params['values']:
            #print(field['field'])
            #print(field['field'].split('_')[0])
            #print(field['value'])
            if field['field'].split('_')[0] != "notes":
                if field['value'] == '' and (field['field'].split('_')[0] == "fromtime" or field['field'].split('_')[0] == "totime"):
                    field_search = request.env['employee.hours'].sudo().search(
                        [('employee_sheet_id', '=', timesheet),
                         ('task_id', '=', int(field['field'].split('_')[1])), ('date', '=',
                                                                               field['field'].split('_')[
                                                                                   2] + '-' +
                                                                               field['field'].split('_')[
                                                                                   3] + '-' +
                                                                               field['field'].split('_')[
                                                                                   4]),
                         (field['field'].split('_')[0], '!=', False)])
                    if field_search:
                        field_instance = request.env['employee.hours'].sudo().browse(field_search[0].id)
                        field_instance.unlink()

                if field['value'] != '' and field['field'].split('_')[2] != 'total':
                    if field['field'].split('_')[0] != 'notes':
                        if field['field'].split('_')[1] != 'other':
                            print('task_id')
                            print(field['field'].split('_')[1])
                            if field['field'].split('_')[0] == "fromtime" or field['field'].split('_')[0] == "totime":
                                field_search = request.env['employee.hours'].sudo().search(
                                    [('employee_sheet_id', '=', timesheet),
                                     ('task_id', '=', int(field['field'].split('_')[1])), ('date', '=',
                                                                                           field['field'].split('_')[
                                                                                               2] + '-' +
                                                                                           field['field'].split('_')[
                                                                                               3] + '-' +
                                                                                           field['field'].split('_')[
                                                                                               4]),
                                     (field['field'].split('_')[0], '!=', False)])
                                fieldvalue = field['field'].split('_')[2] + '-' + field['field'].split('_')[3] + '-' + field['field'].split('_')[4] + ' ' + field['value'] + ':00'
                            else:
                                field_search = request.env['employee.hours'].sudo().search([('employee_sheet_id', '=', timesheet),('task_id','=',int(field['field'].split('_')[1])),('date','=',field['field'].split('_')[2] + '-' + field['field'].split('_')[3] + '-' + field['field'].split('_')[4]),(field['field'].split('_')[0],'!=',False)])
                                # convert fieldvalue to dot separator if comma
                                fieldvalue = field['value'].replace(",", ".")

                            print("before search")
                            print(field_search)
                            print(fieldvalue)
                            if field_search:
                                field_instance = request.env['employee.hours'].sudo().browse(field_search[0].id)
                                if fieldvalue == 0:
                                    field_instance.unlink()
                                else:
                                    field_instance.write({str(field['field'].split('_')[0]): fieldvalue})
                            else:
                                print("in create")
                                hours = request.env['employee.hours'].sudo().create({
                                      'employee_sheet_id': timesheet,
                                      'date':field['field'].split('_')[2] + '-' + field['field'].split('_')[3] + '-' + field['field'].split('_')[4],
                                      'task_id': field['field'].split('_')[1],
                                       field['field'].split('_')[0]:fieldvalue}
                                )
                        else:
                            # convert fieldvalue to dot separator if comma
                            fieldvalue = field['value'].replace(",", ".")
                            field_search = request.env['employee.hours'].sudo().search(
                                [('employee_sheet_id', '=', timesheet),
                                 ('date','=',field['field'].split('_')[2] + '-' + field['field'].split('_')[3] + '-' +
                                        field['field'].split('_')[4]),
                                 (field['field'].split('_')[0], "!=", False)])
                            if field_search:
                                field_instance = request.env['employee.hours'].sudo().browse(field_search[0].id)
                                if fieldvalue == 0:
                                    field_instance.unlink()
                                else:
                                    field_instance.write({field['field'].split('_')[0]: fieldvalue})
                            else:
                                hours = request.env['employee.hours'].sudo().create({
                                    'employee_sheet_id': timesheet,
                                    'date': field['field'].split('_')[2] + '-' + field['field'].split('_')[3] + '-' +
                                            field['field'].split('_')[4],
                                    field['field'].split('_')[0]: fieldvalue}
                                )
            else:
                sheet = request.env['employee.sheet'].sudo().browse(timesheet)
                sheet.sudo().write({'notes': field['value']})


            #print(request.params)
            #if field['field'].split('_')[0]
            # hours = self.env['employee.hours'].create({
            #      'employee_sheet_id': timesheet,
            #      'name': "Test lead new",
            #      'partner_id': self.env.ref("base.res_partner_1").id,
            #      'description': "This is the description of the test new lead.",
            #      'team_id': self.env.ref("sales_team.team_sales_department").id
            #})

        return True

    @http.route(['/my/get_hours/<int:timesheet>'], type='json', auth="user", methods=['POST'], website=True)
    def get_hours(self, timesheet, **kw):
        total = 0
        for field in request.params['values']:
            if field['value'] != '' and field['field'].split('_')[0] != "notes" and field['field'].split('_')[2] == 'total':
                total += float(field['value'])
        sheet = request.env['employee.sheet'].sudo().browse(timesheet)

        if total != sheet.employee.contract_hours * 4:
            return {"total":total,"contract":sheet.employee.contract_hours * 4}
        else:
            return True

    @http.route(['/my/update_holiday_stats'], type='json', auth="user", methods=['POST'], website=True)
    def update_holiday_stats(self, **kw):
        employee = request.env['hr.employee'].sudo().search(
            [('user_id.id', '=', [request.env.user.id])], limit=1)
        holiday_values = employee.calc_vac_hours(request.params['values'].get('ref_date'))
        return {"holiday_values":holiday_values}

    @http.route(['/csv/download/<string:active_ids>'], type='http', auth="user", methods=['GET'], website=True)
    def csv_download(self, active_ids, **kw):
        ids = active_ids.split(",")
        # if ids:
        #     moves = request.env['account.move'].sudo().browse(ids)
        #     print(moves)
        custom_csv = request.env['csv.custom_csv'].sudo().browse(int(active_ids))
        print(custom_csv)
        csv = custom_csv.generate_csv()
        filename = 'exact.csv'
        return request.make_response(csv,
                                     [('Content-Type', 'application/octet-stream'),
                                      ('Content-Disposition', 'attachment; filename="%s"' % (filename))])

    # def account(self):
    #     pass