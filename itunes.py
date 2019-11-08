from appstoreconnect import Api
from collections import defaultdict
from datetime import datetime
from dateutil.relativedelta import relativedelta
import csv
from utils import *

def get(config, dates) :
	#download(config, dates)
	parse(dates)
	return {}

def filename(date) :
	return f'tmp/itunes_{date.year}-{date.month}.csv'

def download(config, dates) :
	print('Connecting to AppStore Connect API...')
	api = Api(config['key_id'], config['key_file'], config['issuer_id'])

	for date in dates :
		# make the actual date and the apple date, we pick a day in the middle
		# of the month to try and avoid any "rounding" issues
		actualDate = datetime(int(date.year), int(date.month), 15)
		# the apple date is offset by a quarter
		appleDate = actualDate + relativedelta(months=3)

		print(f'Getting data for {date.year}-{date.month} ({appleDate.year}-{appleDate.month:02d} in Apples Fiscal Calendar)')

		api.download_finance_reports(
			filters={'vendorNumber': config['vendor_id'],
			'reportDate': f'{appleDate.year}-{appleDate.month:02d}'},
			save_to=filename(date)
		)

def parse(dates) :
	for date in dates : parseSingle(date)

def parseSingle(date) :
	with open(filename(date), newline='') as f:
		reader = csv.DictReader(f, delimiter='\t')

		# this dictionary is keyed on product title
		# each value is yet another dictionary, this time keyed per country of sale (which implies a single currency)
		# these then hold a TransactionCollection that stores count and sum
		products = dict()

		for row in reader:
			# the files contain two tables, once we reach the second one, bail
			if row['Start Date'] == 'Total_Rows' : break

			titleKey = row['Title']
			if not titleKey in products : products[titleKey] = dict()
			title = products[titleKey]

			countryKey = row['Country Of Sale']
			if not countryKey in title : title[countryKey] = TransactionCollection()
			country = title[countryKey]

			country.count += int(row['Quantity'])
			country.sum += Decimal(row['Extended Partner Share'])

	for product, countries in products.items() :
		print(product)
		for country, transactions in countries.items() :
			print()
			print(f'{country}\t{transactions.count}')
			print(f'\t{transactions.sum}')
