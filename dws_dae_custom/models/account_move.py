import re

from odoo import api, fields, models, _
from odoo.tools.misc import str2bool, xlwt
from xlsxwriter.workbook import Workbook
from xlwt import easyxf
import base64
from io import BytesIO
from xml.dom.minidom import Document


class AccountMoveCustom(models.Model):
    _inherit = 'account.move'

    @api.depends('line_ids.debit', 'line_ids.credit')
    def _amount_compute(self):
        for move in self:
            total = 0.0
            for line in move.line_ids:
                total += line.debit
            move.amount = total

    exact_boekstuknummer = fields.Char(compute='_compute_number')
    amount = fields.Monetary(compute='_amount_compute', store=True)
    employee_sheet_id = fields.Many2one('employee.sheet', string='Employee sheet')
    approval_id = fields.Many2one('employee_sheet.approvals', string='Employee sheet approval')

    def _compute_number(self):
        for rec in self:
            input = rec.name
            if input:
                match = re.match('(.*/)(.*)/(.*)', input)
                journal_id = rec.journal_id.id
                prefix = '%03d' % journal_id
                if match:
                    rec.exact_boekstuknummer = str(prefix) + match.group(2) + match.group(3)
                else:
                    rec.exact_boekstuknummer = ""

    def excel_invoice_template_create(self):

        invoice = self
        workbook = xlwt.Workbook()
        worksheet = []
        worksheet.append(0)

        style1 = xlwt.easyxf('pattern: pattern solid, fore_colour gray25;''font:bold True')

        style = xlwt.XFStyle()
        tall_style = xlwt.easyxf('font:height 720;')  # 36pt
        font = xlwt.Font()
        font.name = 'Times New Roman'
        font.bold = True
        font.height = 250
        i = 0
        sheetName = 1

        if invoice.name:
            worksheet[i] = workbook.add_sheet(str(invoice.name))
        else:
            worksheet[i] = workbook.add_sheet(str(sheetName))
            sheetName += 1
        style.font = font
        worksheet[i].write(0, 0, 'Factuurgegevens', style)
        worksheet[i].write(0, 1, 'Waardes', style)
        # first_row = worksheet[i].row(1)
        # first_row.set_style(tall_style)
        first_col = worksheet[i].col(1)
        first_col.width = 156 * 30
        # second_row = worksheet[i].row(0)
        # second_row.set_style(tall_style)
        second_col = worksheet[i].col(0)
        second_col.width = 236 * 30

        worksheet[i].write(1, 0, 'Factuurnummer', style1)
        worksheet[i].write(1, 1, invoice.name or '')
        worksheet[i].write(2, 0, 'Factuurdatum', style1)
        worksheet[i].write(2, 1, str(invoice.invoice_date) or '')
        worksheet[i].write(3, 0, 'Vervaldatum', style1)
        worksheet[i].write(3, 1, str(invoice.invoice_date_due) or '')
        worksheet[i].write(4, 0, 'Debiteurennummer', style1)
        worksheet[i].write(5, 0, 'Ordernummer', style1)
        worksheet[i].write(5, 1, invoice.invoice_line_ids[0].analytic_account_id.name or '')

        worksheet[i].write(7, 0, 'Uw gegevens', style)
        worksheet[i].write(8, 0, 'Naam', style1)
        worksheet[i].write(8, 1, invoice.company_id.name)
        worksheet[i].write(9, 0, 'Adres', style1)
        worksheet[i].write(9, 1, str(invoice.company_id.street or "") + " " + str(invoice.company_id.street2 or ""))
        worksheet[i].write(10, 0, 'Woonplaats', style1)
        worksheet[i].write(10, 1, invoice.company_id.city)
        worksheet[i].write(11, 0, 'Postcode', style1)
        worksheet[i].write(11, 1, invoice.company_id.zip)
        worksheet[i].write(12, 0, 'Telefoonnummer', style1)
        worksheet[i].write(12, 1, invoice.company_id.phone)
        worksheet[i].write(13, 0, 'E-mail', style1)
        worksheet[i].write(13, 1, invoice.company_id.email)
        worksheet[i].write(14, 0, 'IBAN', style1)
        worksheet[i].write(14, 1, invoice.company_id.report_footer.split("IBAN:")[1].split(" ")[0])
        worksheet[i].write(15, 0, 'BIC', style1)
        worksheet[i].write(15, 1, invoice.company_id.report_footer.split("BIC:")[1].split(" ")[0])
        worksheet[i].write(16, 0, 'KvK', style1)
        worksheet[i].write(16, 1, invoice.company_id.company_registry or '')
        worksheet[i].write(17, 0, 'BTW', style1)
        worksheet[i].write(17, 1, invoice.company_id.partner_id.vat or '')

        worksheet[i].write(19, 0, 'Gegevens klant', style)
        worksheet[i].write(20, 0, 'Naam', style1)
        worksheet[i].write(20, 1, invoice.partner_id.name or '')
        worksheet[i].write(21, 0, 'Adres', style1)
        worksheet[i].write(21, 1, str(invoice.partner_id.street or "") + " " + str(invoice.partner_id.street2 or ""))
        worksheet[i].write(22, 0, 'Woonplaats', style1)
        worksheet[i].write(22, 1, invoice.partner_id.city or '')
        worksheet[i].write(23, 0, 'Postcode', style1)
        worksheet[i].write(23, 1, invoice.partner_id.zip or '')
        worksheet[i].write(24, 0, 'KvK', style1)
        if invoice.partner_id.parent_id:
            kvk = invoice.partner_id.parent_id.company_registry
        else:
            kvk = invoice.partner_id.company_registry

        worksheet[i].write(24, 1, kvk or '')

        worksheet[i].write(26, 0, 'Totaalbedragen', style)
        worksheet[i].write(27, 0, 'Incl. BTW', style1)
        if invoice.move_type == 'out_refund':
            worksheet[i].write(27, 1, -invoice.amount_total)
        else:
            worksheet[i].write(27, 1, invoice.amount_total)
        worksheet[i].write(28, 0, 'Excl. BTW', style1)
        if invoice.move_type == 'out_refund':
            worksheet[i].write(28, 1, -invoice.amount_untaxed)
        else:
            worksheet[i].write(28, 1, invoice.amount_untaxed)
        if invoice.move_type == 'out_refund':
            worksheet[i].write(29, 0, '0% BTW-grondslag', style1)
            if invoice.line_ids[0].tax_ids.amount == 0:
                worksheet[i].write(29, 1, -invoice.amount_untaxed)
            worksheet[i].write(30, 0, '9% BTW-bedrag', style1)
            if invoice.line_ids[0].tax_ids.amount == 9:
                worksheet[i].write(30, 1, -invoice.amount_tax)
            worksheet[i].write(31, 0, '9% BTW-grondslag', style1)
            if invoice.line_ids[0].tax_ids.amount == 9:
                worksheet[i].write(31, 1, -invoice.amount_untaxed)
            worksheet[i].write(32, 0, '21% BTW-bedrag', style1)
            if invoice.line_ids[0].tax_ids.amount == 21:
                worksheet[i].write(32, 1, -invoice.amount_tax)
            worksheet[i].write(33, 0, '21% BTW-grondslag', style1)
            if invoice.line_ids[0].tax_ids.amount == 21:
                worksheet[i].write(33, 1, -invoice.amount_untaxed)
        else:
            worksheet[i].write(29, 0, '0% BTW-grondslag', style1)
            if invoice.line_ids[0].tax_ids.amount == 0:
                worksheet[i].write(29, 1, invoice.amount_untaxed)
            worksheet[i].write(30, 0, '9% BTW-bedrag', style1)
            if invoice.line_ids[0].tax_ids.amount == 9:
                worksheet[i].write(30, 1, invoice.amount_tax)
            worksheet[i].write(31, 0, '9% BTW-grondslag', style1)
            if invoice.line_ids[0].tax_ids.amount == 9:
                worksheet[i].write(31, 1, invoice.amount_untaxed)
            worksheet[i].write(32, 0, '21% BTW-bedrag', style1)
            if invoice.line_ids[0].tax_ids.amount == 21:
                worksheet[i].write(32, 1, invoice.amount_tax)
            worksheet[i].write(33, 0, '21% BTW-grondslag', style1)
            if invoice.line_ids[0].tax_ids.amount == 21:
                worksheet[i].write(33, 1, invoice.amount_untaxed)
        worksheet[i].write(35, 0, 'Factuurregels', style)
        row_10 = 35
        row = 1
        for vals in invoice.invoice_line_ids:
            worksheet[i].write(row_10 + 1, 0, 'Regelnummer' + str(row), style1)
            worksheet[i].write(row_10 + 2, 0, 'Totaalprijs regel', style1)
            if invoice.move_type == 'out_refund':
                worksheet[i].write(row_10 + 2, 1, -vals.price_subtotal or 0)
            else:
                worksheet[i].write(row_10 + 2, 1, vals.price_subtotal or 0)
            worksheet[i].write(row_10 + 3, 0, 'Prijs per stuk', style1)
            if vals.price_subtotal < 0:
                worksheet[i].write(row_10 + 3, 1, abs(vals.price_unit) or 0)
            else:
                worksheet[i].write(row_10 + 3, 1, vals.price_unit or 0)
            worksheet[i].write(row_10 + 4, 0, 'Hoeveelheid', style1)
            if vals.price_subtotal < 0 or invoice.move_type == 'out_refund':
                worksheet[i].write(row_10 + 4, 1, -vals.quantity or 0)
            else:
                worksheet[i].write(row_10 + 4, 1, vals.quantity or 0)
            worksheet[i].write(row_10 + 5, 0, 'Beschrijving', style1)
            worksheet[i].write(row_10 + 5, 1, vals.name or 0)
            worksheet[i].write(row_10 + 6, 0, 'BTW-percentage', style1)
            worksheet[i].write(row_10 + 6, 1, vals.tax_ids.amount or 0)
            row_10 += 6
            row += 1

        # worksheet[i].write(2, 5, invoice.date_invoice or '')
        # worksheet[i].write(3, 5, invoice.currency_id.name or '')
        # worksheet[i].write(4, 1, invoice.partner_id.street or '')
        # worksheet[i].write(3, 1, invoice.partner_id.street2 or '')
        # worksheet[i].write(5, 1, invoice.partner_id.city or '')
        # row_10 = 7
        # for vals in invoice.invoice_line_ids:
        #     row_10 += 1
        #     worksheet[i].write(row_10, 1, vals.product_id.name or '')
        #     worksheet[i].write(row_10, 0, vals.product_id.default_code or '')
        #     worksheet[i].write(row_10, 2, vals.quantity or '')
        #     worksheet[i].write(row_10, 3, vals.uom_id.name or '')
        #     worksheet[i].write(row_10, 4, vals.price_unit or '')
        #     worksheet[i].write(row_10, 5, vals.price_subtotal or '')
        #
        # row_10 += 2
        # worksheet[i].write(row_10, 5, invoice.amount_untaxed)
        # worksheet[i].write(row_10 + 1, 5, invoice.amount_total)
        # worksheet[i].write(row_10, 4, 'Untaxed Amount', style)
        # worksheet[i].write(row_10 + 1, 4, 'Total', style)
        i += 1

        fp = BytesIO()
        workbook.save(fp)

        xls = base64.encodebytes(fp.getvalue())
        fp.close()
        return xls
    @staticmethod
    def _append_child(root, parent, child_tag, child_content=None, attr_name=None, attr_val=None):
        child = root.createElement(child_tag)
        if attr_name is not None:
            child.setAttribute(attr_name, attr_val)
        if child_content is not None:
            child_text = root.createTextNode(child_content)
            child.appendChild(child_text)
        parent.appendChild(child)
        return child

    def peppol_invoice_template_create(self,base64pdf,pdf_name):
        invoice = self
        # this must be changed
        country = 'NL'
        company_street = str(invoice.company_id.street or '') + ' ' + str(invoice.company_id.street2 or '')
        partner_street = str(invoice.partner_id.street or '') + ' ' + str(invoice.partner_id.street2 or '')
        company_kvk = str(invoice.company_id.company_registry or '')
        partner_kvk = str(invoice.partner_id.company_registry or '')
        partner_oin = str(invoice.partner_id.company_oin or invoice.partner_id.parent_id.company_oin or '')
        # if VAT is not the same for all invoice lines, changes are needed
        global_vat = invoice.invoice_line_ids[0].tax_ids.amount
        company_iban = invoice.company_id.report_footer.split('IBAN:')[1].split(' ')[0]
        company_btw = invoice.company_id.partner_id.vat
        orderreference = invoice.invoice_line_ids[0].analytic_account_id.name or ''

        root = Document()
        inv = root.createElement('Invoice')
        inv.setAttribute('xmlns', 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2')
        inv.setAttribute('xmlns:cbc', 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2')
        inv.setAttribute('xmlns:cac', 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2')
        root.appendChild(inv)

        self._append_child(root, inv, 'cbc:UBLVersionID', '2.1')
        self._append_child(root, inv, 'cbc:CustomizationID',
                           'urn:cen.eu:en16931:2017#compliant#urn:fdc:nen.nl:nlcius:v1.0')
        self._append_child(root, inv, 'cbc:ProfileID', 'urn:fdc:peppol.eu:2017:poacc:billing:01:1.0')

        self._append_child(root, inv, 'cbc:ID', invoice.name)
        self._append_child(root, inv, 'cbc:IssueDate', str(invoice.invoice_date))
        self._append_child(root, inv, 'cbc:DueDate', str(invoice.invoice_date_due))

        self._append_child(root, inv, 'cbc:InvoiceTypeCode', '380')
        self._append_child(root, inv, 'cbc:DocumentCurrencyCode', 'EUR')
        self._append_child(root, inv, 'cbc:BuyerReference','-')
        cac_orderreference = self._append_child(root, inv, 'cac:OrderReference')
        self._append_child(root, cac_orderreference, 'cbc:ID', str(orderreference))

        cac_additional_document_reference = self._append_child(root, inv, 'cac:AdditionalDocumentReference')
        self._append_child(root, cac_additional_document_reference, 'cbc:ID', pdf_name)
        # change with the real pdf content
        cac_attachment = self._append_child(root, cac_additional_document_reference, 'cac:Attachment')

        self._append_child(root, cac_attachment, 'cbc:EmbeddedDocumentBinaryObject', base64pdf.decode('utf-8'),'mimeCode','application/pdf')
        cac_accounting_supplier_party = self._append_child(root, inv, 'cac:AccountingSupplierParty')
        cac_party = self._append_child(root, cac_accounting_supplier_party, 'cac:Party')
        self._append_child(root, cac_party, 'cbc:EndpointID', company_kvk, 'schemeID', '0106')
        cac_party_identification = self._append_child(root, cac_party, 'cac:PartyIdentification')
        self._append_child(root, cac_party_identification, 'cbc:ID', company_kvk, 'schemeID', '0106')
        cac_party_name = self._append_child(root, cac_party, 'cac:PartyName')
        self._append_child(root, cac_party_name, 'cbc:Name', invoice.company_id.name)

        cac_postal_address = self._append_child(root, cac_party, 'cac:PostalAddress')
        self._append_child(root, cac_postal_address, 'cbc:StreetName', company_street)
        self._append_child(root, cac_postal_address, 'cbc:CityName', invoice.company_id.city)
        self._append_child(root, cac_postal_address, 'cbc:PostalZone', invoice.company_id.zip)
        cac_country = self._append_child(root, cac_postal_address, 'cac:Country')
        self._append_child(root, cac_country, 'cbc:IdentificationCode', country)

        cac_party_tax_scheme = self._append_child(root, cac_party, 'cac:PartyTaxScheme')
        self._append_child(root, cac_party_tax_scheme, 'cbc:CompanyID', company_btw)
        cac_tax_scheme = self._append_child(root, cac_party_tax_scheme, 'cac:TaxScheme')
        self._append_child(root, cac_tax_scheme, 'cbc:ID', 'VAT')

        cac_party_legal_entity = self._append_child(root, cac_party, 'cac:PartyLegalEntity')
        self._append_child(root, cac_party_legal_entity, 'cbc:RegistrationName', invoice.company_id.name)
        self._append_child(root, cac_party_legal_entity, 'cbc:CompanyID', company_kvk, 'schemeID', '0106')
        cac_contact = self._append_child(root, cac_party, 'cac:Contact')
        self._append_child(root, cac_contact, 'cbc:ElectronicMail', invoice.company_id.email)

        cac_accounting_customer_party = self._append_child(root, inv, 'cac:AccountingCustomerParty')
        cac_party = self._append_child(root, cac_accounting_customer_party, 'cac:Party')

        if partner_oin != '':
            self._append_child(root, cac_party, 'cbc:EndpointID', partner_oin, 'schemeID', '0190')
        else:
            self._append_child(root, cac_party, 'cbc:EndpointID', partner_kvk, 'schemeID', '0106')
        cac_party_identification = self._append_child(root, cac_party, 'cac:PartyIdentification')

        if partner_oin != '':
            self._append_child(root, cac_party_identification, 'cbc:ID', partner_oin, 'schemeID', '0190')
        else:
            self._append_child(root, cac_party_identification, 'cbc:ID', partner_kvk, 'schemeID', '0106')

        cac_party_name = self._append_child(root, cac_party, 'cac:PartyName')
        self._append_child(root, cac_party_name, 'cbc:Name', invoice.partner_id.name)

        cac_postal_address = self._append_child(root, cac_party, 'cac:PostalAddress')
        self._append_child(root, cac_postal_address, 'cbc:StreetName', partner_street)
        self._append_child(root, cac_postal_address, 'cbc:CityName', invoice.partner_id.city)
        self._append_child(root, cac_postal_address, 'cbc:PostalZone', invoice.partner_id.zip)
        cac_country = self._append_child(root, cac_postal_address, 'cac:Country')
        self._append_child(root, cac_country, 'cbc:IdentificationCode', country)

        cac_party_legal_entity = self._append_child(root, cac_party, 'cac:PartyLegalEntity')
        self._append_child(root, cac_party_legal_entity, 'cbc:RegistrationName', invoice.partner_id.name)
        
        if partner_oin != '':
            self._append_child(root, cac_party_legal_entity, 'cbc:CompanyID', partner_oin, 'schemeID', '0190')
        else:
            self._append_child(root, cac_party_legal_entity, 'cbc:CompanyID', partner_kvk, 'schemeID', '0106')

        cac_payment_means = self._append_child(root, inv, 'cac:PaymentMeans')
        self._append_child(root, cac_payment_means, 'cbc:PaymentMeansCode', '57')
        cac_payee_financial_account = self._append_child(root, cac_payment_means, 'cac:PayeeFinancialAccount')
        self._append_child(root, cac_payee_financial_account, 'cbc:ID', company_iban)

        cac_tax_total = self._append_child(root, inv, 'cac:TaxTotal')
        self._append_child(root, cac_tax_total, 'cbc:TaxAmount', str(invoice.amount_tax if invoice.move_type != 'out_refund' else -abs(invoice.amount_tax)), 'currencyID', 'EUR')
        cac_tax_subtotal = self._append_child(root, cac_tax_total, 'cac:TaxSubtotal')
        self._append_child(root, cac_tax_subtotal, 'cbc:TaxableAmount', str(invoice.amount_untaxed if invoice.move_type != 'out_refund' else -abs(invoice.amount_untaxed)), 'currencyID',
                           'EUR')
        self._append_child(root, cac_tax_subtotal, 'cbc:TaxAmount', str(invoice.amount_tax if invoice.move_type != 'out_refund' else -abs(invoice.amount_tax)), 'currencyID', 'EUR')
        cac_tax_category = self._append_child(root, cac_tax_subtotal, 'cac:TaxCategory')
        self._append_child(root, cac_tax_category, 'cbc:ID', 'S')
        self._append_child(root, cac_tax_category, 'cbc:Percent', str(global_vat))
        cac_tax_scheme = self._append_child(root, cac_tax_category, 'cac:TaxScheme')
        self._append_child(root, cac_tax_scheme, 'cbc:ID', 'VAT', 'schemeID', 'UN/ECE 5153')

        cac_legal_monetary_total = self._append_child(root, inv, 'cac:LegalMonetaryTotal')
        self._append_child(root, cac_legal_monetary_total, 'cbc:LineExtensionAmount', str(invoice.amount_untaxed if invoice.move_type != 'out_refund' else -abs(invoice.amount_untaxed)),
                           'currencyID', 'EUR')
        self._append_child(root, cac_legal_monetary_total, 'cbc:TaxExclusiveAmount', str(invoice.amount_untaxed if invoice.move_type != 'out_refund' else -abs(invoice.amount_untaxed)),
                           'currencyID', 'EUR')
        self._append_child(root, cac_legal_monetary_total, 'cbc:TaxInclusiveAmount', str(invoice.amount_total if invoice.move_type != 'out_refund' else -abs(invoice.amount_total)),
                           'currencyID', 'EUR')
        self._append_child(root, cac_legal_monetary_total, 'cbc:PayableAmount', str(invoice.amount_total if invoice.move_type != 'out_refund' else -abs(invoice.amount_total)), 'currencyID',
                           'EUR')

        for invoice_line in invoice.invoice_line_ids:
            cac_invoice_line = self._append_child(root, inv, 'cac:InvoiceLine')
            self._append_child(root, cac_invoice_line, 'cbc:ID', '1')
            self._append_child(root, cac_invoice_line, 'cbc:InvoicedQuantity', str(invoice_line.quantity), 'unitCode',
                               'ZZ')
            self._append_child(root, cac_invoice_line, 'cbc:LineExtensionAmount', str(invoice_line.price_subtotal if invoice.move_type != 'out_refund' else -abs(invoice_line.price_subtotal)),
                               'currencyID', 'EUR')

            cac_item = self._append_child(root, cac_invoice_line, 'cac:Item')
            self._append_child(root, cac_item, 'cbc:Name', invoice_line.name)
            cac_classified_tax_category = self._append_child(root, cac_item, 'cac:ClassifiedTaxCategory')
            self._append_child(root, cac_classified_tax_category, 'cbc:ID', 'S')
            self._append_child(root, cac_classified_tax_category, 'cbc:Percent', str(invoice_line.tax_ids.amount))
            cac_tax_scheme = self._append_child(root, cac_classified_tax_category, 'cac:TaxScheme')
            self._append_child(root, cac_tax_scheme, 'cbc:ID', 'VAT', 'schemeID', 'UN/ECE 5153')

            cac_price = self._append_child(root, cac_invoice_line, 'cac:Price')
            self._append_child(root, cac_price, 'cbc:PriceAmount', str(invoice_line.price_unit), 'currencyID', 'EUR')
            self._append_child(root, cac_price, 'cbc:BaseQuantity', str(invoice_line.quantity), 'unitCode', 'ZZ')

        # change name as needed and return what you need
        xml_str = root.toprettyxml(indent='\t')
        xml = base64.encodebytes(xml_str.encode('utf-8'))
        return xml