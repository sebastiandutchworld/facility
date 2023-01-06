# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from multiprocessing import resource_tracker
import random
import io
import xlrd
import babel
import logging
import tempfile
import binascii
import re
import time
from io import StringIO
from datetime import date, datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import Warning, UserError, ValidationError
import threading
_logger = logging.getLogger(__name__)

try:
	import csv
except ImportError:
	_logger.debug('Cannot `import csv`.')
try:
	import xlwt
except ImportError:
	_logger.debug('Cannot `import xlwt`.')
try:
	import cStringIO
except ImportError:
	_logger.debug('Cannot `import cStringIO`.')
try:
	import base64
except ImportError:
	_logger.debug('Cannot `import base64`.')


class SaleOrderCounter():
    def __init__(self):
        self.count = 0

    def increment(self):
        self.count += 1

    def get_count(self):
        return self.count

class ImportSaleorder(models.TransientModel):
	_name = 'import.saleorder'
	_description = 'Import Saleorder'

	errors = []
	warnings = []

	file = fields.Binary(string="Upload File")


	fields_sale_order = ['Contract Name', 'Customer', 'Company', 'Pricelist', 'Order Lines/Product Template/Internal Reference',
		 'Order Lines/Quantity', 'Order Lines/Unit Price', 'Internal Reference', 'Name', 'Barcode', 'NSN', 'Purchase Unit of Measure',
		  'Unit of Measure', 'Product Conditions/Code', 'Cost', 'Product Type', 'Routes','company_id', 'Tracking', 'Vendor',
		   'Product Template/Internal Reference', 'Vendor Product Code', 'Vendor Product Name', 'Currency', 'Company','Quantity','Price','Start Date','End Date','Delivery Lead Time']

	fields_sale_order_line = ['Order Lines/Product Template/Internal Reference', 'Order Lines/Quantity',  'Order Lines/Unit Price',
		   'Internal Reference','Name','Barcode','NSN',	'Purchase Unit of Measure', 'Unit of Measure','Product Conditions/Code',
			'Cost', 'Product Type', 'Routes', 'company_id', 'Tracking','Vendor','Product Template/Internal Reference',
			'Vendor Product Code', 'Vendor Product Name', 'Currency','Company', 'Quantity','Price','Start Date','End Date','Delivery Lead Time']

	def progressbar(self, sale_orders, counter, label):
		j = 1
		for sale_order in self.web_progress_iter(sale_orders, msg=label):
			j = j + 1
			while 1 == 1:
				time.sleep(0.005)
				if counter.get_count() > j or counter.get_count() == len(sale_orders):
					break

	# odoo progress bar
	def web_progress_iter(self, iterable, msg=""):
		"""Wrapper around iter() that yields the number of iterations."""
		if self._context.get('import_file'):
			total = len(iterable)
			for i, item in enumerate(iterable):
				yield item
				self._cr.commit()
				self.env['import.saleorder'].browse(self._context.get('import_file')).write({'progress': int((i + 1) * 100 / total)})
		else:
			for item in iterable:
				yield item


	def import_saleorders(self):
		error_bool = True;	
		sale_order_name = ""
		pricelist_name, pricelist_currency = "" , ""
		self.errors.clear()

		if not self.file:
			raise ValidationError(_("Please Upload File to Import Sale orders !"))

		try:
			file = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
			file.write(binascii.a2b_base64(self.file))
			file.seek(0)
			values = {}
			workbook = xlrd.open_workbook(file.name)
			sheet = workbook.sheet_by_index(0)
		except Exception:
			raise ValidationError(_("Please Select Valid File Format !"))


		for row_no in range(sheet.nrows):
			values = list(map(lambda row:row.value, sheet.row(row_no)))
			sale_order_line_values = values[4:]
			
			self.check_missing_fields(row_no, values)
			self.raise_error(enable_error_message = error_bool)
			
			self.check_values_SO(row_no, values)
			self.raise_error(enable_error_message = error_bool)
			
			self.check_values_SO_line(row_no, sale_order_line_values)
			self.raise_error(enable_error_message = error_bool)

			if row_no == 1:
				pricelist_name, pricelist_currency = self.check_if_pricelist_exists(row_no, values)
				self.raise_error(enable_error_message = error_bool)
				sale_order_name = self.check_latest_sale_order_line_create_new_name(row_no, values)
				self.raise_error(enable_error_message = error_bool)


			self.check_if_vendor_exist(row_no, sale_order_line_values)
			self.raise_error(enable_error_message = error_bool)

			self.check_if_partner_exist(row_no, values)
			self.raise_error(enable_error_message = error_bool)

			self.check_if_product_exists(row_no, sale_order_line_values)
			self.raise_error(enable_error_message = error_bool)

			self.create_Sale_order(row_no, values, sale_order_name, pricelist_name)
			self.raise_error(enable_error_message = error_bool)

			self.add_sale_order_lines(row_no, sale_order_line_values, sale_order_name)
			self.raise_error(enable_error_message = error_bool)

		
		return 0

	def check_missing_fields(self, row_no, values):
		if row_no == 0:
			for index, field in enumerate(self.fields_sale_order):
				if str(field) not in values:
					self.errors.append("Missing mandatory field : " + str(field))
	
	def values_filler(self, values, fields):
		if values[fields.index('NSN')] == "":
			values[fields.index('NSN')] = " "
		if values[fields.index('Vendor')] == "":
			values[fields.index('Vendor')] = " "
		if values[fields.index('Product Template/Internal Reference')] == "":
			values[fields.index('Product Template/Internal Reference')] = " "
		if values[fields.index('Vendor Product Name')] == "":
			values[fields.index('Vendor Product Name')] = " "
		if values[fields.index('Vendor Product Code')] == "":
			values[fields.index('Vendor Product Code')] = " "
		if values[fields.index('Currency')] == "":
			values[fields.index('Currency')] = " "		
		if values[fields.index('Quantity') - 1] == "": #company vendor
			values[fields.index('Quantity') - 1] = " "
		if values[fields.index('Quantity')] == "":
			values[fields.index('Quantity')] = " "
		if values[fields.index('Price')] == "":
			values[fields.index('Price')] = " "
		if values[fields.index('Start Date')] == "":
			values[fields.index('Start Date')] = " "
		if values[fields.index('End Date')] == "":
			values[fields.index('End Date')] = " "
		if values[fields.index('Delivery Lead Time')] == "":
			values[fields.index('Delivery Lead Time')] = " "
		
		return values
		

	def comma_to_dot(self, values, fields):
		if values[fields.index('Price')] != "":
			values[fields.index('Price')] = str(values[fields.index('Price')]).replace(",",".")
		if values[fields.index('Cost')] != "":
			values[fields.index('Cost')] = str(values[fields.index('Cost')]).replace(",",".")
		if values[fields.index('Order Lines/Quantity')] != "":
			values[fields.index('Order Lines/Quantity')] = str(values[fields.index('Order Lines/Quantity')]).replace(",",".")
		
		return values



	def check_textfield(self, row_no, values, fields, field_name):
		if values[fields.index(field_name)] != "":
			if not isinstance(values[fields.index(field_name)], str):
				values[fields.index(field_name)] = str(values[fields.index(field_name)])
	
	def check_num_field(self, row_no, values, fields, field_name):
		if values[fields.index(field_name)] != "":
			if not isinstance(values[fields.index(field_name)], int) and not isinstance(values[fields.index(field_name)], float):
				values[fields.index(field_name)] = float(values[fields.index(field_name)])
				
	
	def check_textfields(self, row_no, values, fields):
		self.check_textfield(row_no, values, fields, 'Order Lines/Product Template/Internal Reference')
		self.check_textfield(row_no, values, fields, 'Internal Reference')
		self.check_textfield(row_no, values, fields, 'Barcode')
		self.check_textfield(row_no, values, fields, 'NSN')
		self.check_textfield(row_no, values, fields, 'Product Template/Internal Reference')
	
	def check_num_fields(self, row_no, values, fields):
		self.check_num_field(row_no, values, fields, 'Order Lines/Quantity')
		self.check_num_field(row_no, values, fields, 'Order Lines/Price')
		self.check_num_field(row_no, values, fields, 'Order Lines/Cost')
		self.check_num_field(row_no, values, fields, 'Quantity')
		self.check_num_field(row_no, values, fields, 'Price')
		self.check_num_field(row_no, values, fields, 'Cost')


	def remove_non_numeric_prefix_suffix(self, values, fields, field_name):
		if values[fields.index(field_name)] != "" and values[fields.index(field_name)] != " ":
			while(not values[fields.index(field_name)][0].isdigit()):
				values[fields.index(field_name)] = values[fields.index(field_name)][1:]
			while(not values[fields.index(field_name)][-1].isdigit()):
				values[fields.index(field_name)] = values[fields.index(field_name)][:-1]
		return values

	def check_nsn(self, row_no, values, fields):
		if values[fields.index('NSN')] == "" or values[fields.index('NSN')] == " ":
			return values

		values = self.remove_non_numeric_prefix_suffix(values, fields, field_name = 'NSN')

		#check how many characters are in the string without dashes
		nsn_string = values[fields.index('NSN')].replace("-","")
		
		if len(nsn_string) != 13:
			self.errors.append("Row " + str(row_no) + " : NSN must be 13 characters long !")
			self.errors.append("nsn_string = " + nsn_string)
		
		return values

	def check_values_SO(self,row_no, values):
		if row_no == 1:
			values = self.values_filler(values, self.fields_sale_order)
			values = self.comma_to_dot(values, self.fields_sale_order)
			self.check_textfields(row_no, values, self.fields_sale_order)
			# self.check_num_fields(row_no, values, self.fields_sale_order)
			values = self.check_nsn(row_no, values, self.fields_sale_order)
			values = self.remove_non_numeric_prefix_suffix(values, self.fields_sale_order, field_name = 'Order Lines/Quantity')
			values = self.remove_non_numeric_prefix_suffix(values, self.fields_sale_order, field_name = 'Cost')
			values = self.remove_non_numeric_prefix_suffix(values, self.fields_sale_order, field_name = 'Price')

			for index, value in enumerate(values):
				if value == '':
					self.errors.append("Missing sale order value for field : " + str(self.fields_sale_order[index]))				
				if value == ' ':
					value = ''


	def check_values_SO_line(self,row_no, values):
		if row_no > 1:
			values = self.values_filler(values, self.fields_sale_order_line)
			values = self.comma_to_dot(values, self.fields_sale_order_line)
			self.check_textfields(row_no, values, self.fields_sale_order_line)
			# self.check_num_fields(row_no, values, self.fields_sale_order_line)
			values = self.check_nsn(row_no, values, self.fields_sale_order_line)
			values = self.remove_non_numeric_prefix_suffix(values, self.fields_sale_order_line, field_name = 'Order Lines/Quantity')
			values = self.remove_non_numeric_prefix_suffix(values, self.fields_sale_order_line, field_name = 'Cost')
			values = self.remove_non_numeric_prefix_suffix(values, self.fields_sale_order_line, field_name = 'Price')

			for index, value in enumerate(values):
				if value == '':
					self.errors.append("[" + str(row_no) + "][" + str(index) + "]Missing sale order line value for field : " + str(self.fields_sale_order_line[index]))
				if value == ' ':
					value = ''
				
	def check_if_pricelist_exists(self, row_no, values):
		pricelist, pricelist_name, pricelist_currency = "", "", ""
		pricelist = values[self.fields_sale_order.index('Pricelist')]
		if '(' in pricelist and ')' in pricelist:
			pricelist_name, pricelist_currency = pricelist.split(" (")[0], pricelist.split("(")[1]
			pricelist_currency = pricelist_currency.split(")")[0]
		else:
			pricelist_name = pricelist

		#search for pricelist limit to one result
		if not self.env['product.pricelist'].search([('name','=',pricelist_name)],limit=1):
		
			self.errors.append("Pricelist: '" + str(pricelist) + "' does not exist")
			return pricelist_name, pricelist_currency
		
		return pricelist_name, pricelist_currency

	def check_if_vendor_exist(self, row_no, values):
		if row_no > 0:
			vendor = values[self.fields_sale_order_line.index('Vendor')]
			if vendor != "" and vendor != " ":
				if not self.env['res.partner'].search([('name','=',vendor)], limit=1):
					self.errors.append("Vendor '" + str(vendor) + "' does not exist")

	def check_if_partner_exist(self, row_no, values):
		if row_no == 1:
			partner = values[1]
			if not self.env['res.partner'].search([('name','=', partner)],limit=1):
				self.errors.append("Partner '" + str(partner) + "' does not exist")

	#internal reference has to be unique
	def check_if_internal_reference_exist(self, values):		
		internal_reference = values[self.fields_sale_order_line.index('Internal Reference')]
		if self.env['product.product'].search([('default_code','=', internal_reference)],limit=1):
			return True, self.env['product.product'].search([('default_code','=', internal_reference)],limit=1).name
		else:
			return False, ""
	
	def check_if_barcode_exists(self, values):
		barcode = values[self.fields_sale_order_line.index('Barcode')]
		if self.env['product.product'].search([('barcode','=', barcode)]):
			return True, self.env['product.product'].search([('barcode','=', barcode)]).name
		else:
			return False, ""

	def check_if_product_exists(self, row_no, values):
		if row_no >= 1:			
			internal_reference_bool, internal_reference_name = self.check_if_internal_reference_exist(values) 
			barcode_bool, barcode_name = self.check_if_barcode_exists(values)

			if internal_reference_bool and barcode_bool:
				if internal_reference_name == barcode_name:
					self.update_vendor_pricelist(row_no, values)

					return True
				else:
					self.errors.append("[" + str(row_no) + "] conflict with adding product to sale-order, Internal Reference and Barcode" + 
					"\ninternal_reference is assigned to: " + str(internal_reference_name) +
					 "\n barcode is assigned to: " + str(barcode_name))
					return False
			elif not internal_reference_bool and not barcode_bool:
				self.create_missing_products(values)
				
			else:
				self.errors.append("Product with internal reference: " + str(values[self.fields_sale_order_line.index('Internal Reference')]) + 
				" belongs to :" + str(internal_reference_name) +
				"\n or barcode : " + str(values[self.fields_sale_order_line.index('Barcode')]) +
				" belongs to :" + str(barcode_name) +
				 "\n please check the product on row: " + str(row_no) + " of the excelsheet and fix inconsistencies, all listed codes should be unique and belong to the same product")
				return False

	def create_missing_products(self, values):
		product_type_string = values[self.fields_sale_order_line.index('Product Type')]
		product_type = "consu"
		if product_type_string == 'Consumable':
			product_type = 'consu'
		elif product_type_string == 'Service':
			product_type = 'service'
		elif product_type_string == 'Storable Product':
			product_type = 'product'
		
		tracking_string = values[self.fields_sale_order_line.index('Tracking')]
		
		if tracking_string == 'By Unique Serial Number':
			tracking_type = 'serial'
		elif tracking_string == 'By Lots':
			tracking_type = 'lot'
		else:
			tracking_type = 'none'

		routing_list = values[self.fields_sale_order_line.index('Routes')].split(',') 
		routing_so_val = []
		
		if "Buy" in routing_list:
			val = self.env['stock.location.route'].search([('name','=','Buy')], limit=1).id
			if val != False:
				routing_so_val.append((4, val))			
			val = self.env['stock.location.route'].search([('name','=','Kopen')], limit=1).id
			if val != False:
				routing_so_val.append((4, val))
		if "Replenish on Order (MTO)" in routing_list:
			val = self.env['stock.location.route'].search([('name','like','(MTO)')], limit=1).id
			if val != False:
				routing_so_val.append((4, val))
		
		self.env['product.template'].create({
			'nsn': values[self.fields_sale_order_line.index('NSN')], 
			'default_code':values[self.fields_sale_order_line.index('Internal Reference')],
		    'name': values[self.fields_sale_order_line.index('Name')],
			'barcode': values[self.fields_sale_order_line.index('Barcode')],
			'uom_id': self.env['uom.uom'].search([('name','=',values[self.fields_sale_order_line.index('Unit of Measure')])]).id,
			'uom_po_id': self.env['uom.uom'].search([('name','=',values[self.fields_sale_order_line.index('Purchase Unit of Measure')])]).id,
			'product_conditions':self.env['product.condition'].search([('code','=',values[self.fields_sale_order_line.index('Product Conditions/Code')])]).id,
			'standard_price':values[self.fields_sale_order_line.index('Cost')],
			'company_id':self.env['res.company'].search([('name','=',values[self.fields_sale_order_line.index('company_id')])]).id, 
			'detailed_type':product_type,
			'tracking':tracking_type,
			'route_ids':routing_so_val,			
			'list_price': 0.0,
			})
	
	def create_vendor_pricelist(self, values):
		vendor_pricelist = self.env['product.supplierinfo'].create({
				'name': self.env['res.partner'].search([('name','=',values[self.fields_sale_order_line.index('Vendor')])],limit=1).id,
				'currency_id': self.env['res.currency'].search([('name','=',values[self.fields_sale_order_line.index('Currency')])],limit=1).id,
				'price': values[self.fields_sale_order_line.index('Price')],
				'product_uom': self.env['uom.uom'].search([('name','=', values[self.fields_sale_order_line.index('Purchase Unit of Measure')])],limit=1).id,
				'min_qty':values[self.fields_sale_order_line.index('Quantity')],
				'product_tmpl_id':self.env['product.template'].search([('barcode','=',values[self.fields_sale_order_line.index('Barcode')])],limit=1).id,
				})

		if values[self.fields_sale_order_line.index('Vendor Product Code')] != '' and values[self.fields_sale_order_line.index('Vendor Product Code')] != ' ':
			vendor_pricelist.product_code = values[self.fields_sale_order_line.index('Vendor Product Code')]
		
		if values[self.fields_sale_order_line.index('Vendor Product Name')] != '' and values[self.fields_sale_order_line.index('Vendor Product Name')] != ' ':
			vendor_pricelist.product_name = values[self.fields_sale_order_line.index('Vendor Product Name')]

		if values[self.fields_sale_order_line.index('Start Date')] != '' and values[self.fields_sale_order_line.index('Start Date')] != ' ':
			start_date = datetime.strptime(values[self.fields_sale_order_line.index('Start Date')], '%d-%m-%Y')
			vendor_pricelist.write({'date_start': start_date})

		if values[self.fields_sale_order_line.index('End Date')] != '' and values[self.fields_sale_order_line.index('End Date')] != ' ':
			end_date = datetime.strptime(values[self.fields_sale_order_line.index('End Date')], '%d-%m-%Y')
			vendor_pricelist.write({'date_end': end_date})
		
		if values[self.fields_sale_order_line.index('Delivery Lead Time')] != '' and values[self.fields_sale_order_line.index('Delivery Lead Time')] != ' ':
			vendor_pricelist.write({'delay': int(values[self.fields_sale_order_line.index('Delivery Lead Time')])})

	def check_date_validity_pricelist(self, pricelists, values):
		for index, pricelist in enumerate(pricelists):
			if str(pricelist.price) == str(values[self.fields_sale_order_line.index('Price')]) and \
				str(pricelist.currency_id.name) == str(values[self.fields_sale_order_line.index('Currency')]) and \
					str(pricelist.product_uom.name) == str(values[self.fields_sale_order_line.index('Purchase Unit of Measure')]) and \
						str(pricelist.min_qty) == str(values[self.fields_sale_order_line.index('Quantity')]) and \
							str(pricelist.name.name) == str(values[self.fields_sale_order_line.index('Vendor')]):
					
				if values[self.fields_sale_order_line.index('Start Date')] != '' and values[self.fields_sale_order_line.index('Start Date')] != ' ':
					if str(type(pricelist.date_start)) == "<class 'datetime.date'>" and \
						pricelist.date_start > datetime.date(datetime.strptime(values[self.fields_sale_order_line.index('Start Date')], '%d-%m-%Y')):
						pricelist.write({'date_start': datetime.strptime(values[self.fields_sale_order_line.index('Start Date')], '%d-%m-%Y')})
					
				if values[self.fields_sale_order_line.index('End Date')] != '' and values[self.fields_sale_order_line.index('End Date')] != ' ':
					if str(type(pricelist.date_end)) == "<class 'datetime.date'>" and \
						pricelist.date_end < datetime.date(datetime.strptime(values[self.fields_sale_order_line.index('End Date')], '%d-%m-%Y')):
						pricelist.write({'date_end': datetime.strptime(values[self.fields_sale_order_line.index('End Date')], '%d-%m-%Y')})
			else:
				self.create_vendor_pricelist(values)
				

	def update_vendor_pricelist(self, row_no, values):
		barcode = values[self.fields_sale_order_line.index('Barcode')]
		vendor = values[self.fields_sale_order_line.index('Vendor')]
		vendor_product_template = values[self.fields_sale_order_line.index('Product Template/Internal Reference')]
		vendor_currency_id = values[self.fields_sale_order_line.index('Currency')]
		vendor_price = values[self.fields_sale_order_line.index('Price')]
		vendor_quantity = values[self.fields_sale_order_line.index('Quantity')]
		vendor_pricelist = self.env['product.supplierinfo'].search([('product_tmpl_id.barcode','=',barcode),('name.name','=',vendor)])

		if vendor != '' and vendor != ' ' and vendor_product_template != '' and vendor_product_template != ' ' and \
			vendor_currency_id != '' and vendor_currency_id != ' ' and vendor_price != '' and vendor_price != ' ' and \
				vendor_quantity != '' and vendor_quantity != ' ':
			
			if len(vendor_pricelist) >= 1:
				self.check_date_validity_pricelist(vendor_pricelist,values)
			if len(vendor_pricelist) == 0:
				self.create_vendor_pricelist(values)

	def check_latest_sale_order_line_create_new_name(self, row_no, values):
		if row_no == 1:
			#retrieve latest saleorder number where the names starts with'SO' & 'DPT
			sale_order_name_daedaelus = self.env['sale.order'].search([('name','like','SO'),('company_id','=','Daedalus')], order='name desc', limit=1).name
			sale_order_name_DPT = self.env['sale.order'].search([('name','like','DPT'),('company_id','like','Daedalus Projects & Trade')], order='name desc', limit=1).name
			
			#check if sale_order_name_daedaelus is a boolean
			if sale_order_name_daedaelus != False:
				sale_order_name_daedaelus = sale_order_name_daedaelus.split('SO')[1]
				sale_order_name_daedaelus = int(sale_order_name_daedaelus) + 1		
				sale_order_name_daedaelus = 'SO' + str(sale_order_name_daedaelus)

			if sale_order_name_DPT != False:
				sale_order_name_DPT = sale_order_name_DPT.split('DPT')[1]
				sale_order_name_DPT = int(sale_order_name_DPT) + 1
				sale_order_name_DPT = 'DPT' + str(sale_order_name_DPT).zfill(4)
			
			if sale_order_name_DPT == False:
				sale_order_name_DPT = 'DPT0001'
			if sale_order_name_daedaelus == False:
				sale_order_name_daedaelus = 'SO1'
			
			#return the latest saleorder number based on the company_id
			if values[self.fields_sale_order.index('company_id')] == 'Daedaelus':
				return sale_order_name_daedaelus
			elif values[self.fields_sale_order.index('company_id')] == 'Daedalus Projects & Trade':
				return sale_order_name_DPT
			else:
				return sale_order_name_daedaelus

	def create_Sale_order(self, row_no, values, sale_order_name, pricelist_name):
		if row_no == 1:
			SO = self.env['sale.order']		
			SO.create({'name': sale_order_name, 
				'partner_id': self.env['res.partner'].search([('name','=',values[1])],limit=1).id,
				'contract_name': values[0],
				'pricelist_id': self.env['product.pricelist'].search([('name','=',pricelist_name)],limit=1).id,
				})


	def add_sale_order_lines(self, row_no, values, sale_order_name):
		if row_no >= 1:
			order_id = self.env['sale.order'].search([('name','=',sale_order_name)]).id
			tax_id = self.env['account.tax'].search([('name','=','Verkopen/omzet hoog')])

			if row_no == 1:
				order_id = self.env['sale.order'].search([('name','=',sale_order_name)]).id
				self.env['sale.order.line'].create({
						'order_id': order_id,						
						'product_id': self.env['product.product'].search([('barcode','=',values[self.fields_sale_order_line.index('Barcode')])]).id,
						'name': self.env['product.product'].search([('barcode','=',values[self.fields_sale_order_line.index('Barcode')])]).name,
						'product_uom_qty': values[self.fields_sale_order_line.index('Order Lines/Quantity')],
						'price_unit': values[self.fields_sale_order_line.index('Order Lines/Unit Price')],
					})
			elif row_no > 1:
				self.env['sale.order.line'].create({
					'order_id': order_id,
					'product_id': self.env['product.product'].search([('barcode','=',values[self.fields_sale_order_line.index('Barcode')])]).id,
					'name': self.env['product.product'].search([('barcode','=',values[self.fields_sale_order_line.index('Barcode')])]).name,
					'product_uom_qty': values[self.fields_sale_order_line.index('Order Lines/Quantity')],
					'price_unit': values[self.fields_sale_order_line.index('Order Lines/Unit Price')],
					})
	
	def check_if_vendor_exists(self, values):
		vendor = values[self.fields_sale_order_line.index('Vendor')]
		if not self.env['res.partner'].search([('name','=',vendor)]):
			self.errors.append("Vendor " + str(vendor) + " does not exist")
	
	def print_all_values(self, values,fields):
		for index, value in enumerate(values):
			print(fields[index] + " = " + str(value))
		
	def raise_error(self, enable_error_message):
		if len(self.errors) > 0 and enable_error_message:
			all_errors = "\n".join(self.errors)
			raise ValidationError(all_errors)


