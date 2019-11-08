from appstoreconnect import Api
from collections import defaultdict
from datetime import datetime
from dateutil.relativedelta import relativedelta
import csv
from utils import *
import re

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
	# first, we parse the data we can get from the API
	# this contains sales (currency and count) per country and product
	# but is missing data of what exactly was paid
	# that file needs to be manually retrieved from app store connect

	# this dictionary is keyed on product title
	# each value is yet another dictionary, this time keyed per currency (which can include many countries)
	# these then hold a TransactionCollection that stores count and sum
	products = dict()

	# we keep a second dictionary for data from the payout csv
	# this stores the earned amount in the local currency, the unit count and most
	# importantly the actual payout amount
	currencies = defaultdict(TransactionCollection)

	with open(filename(date), newline='') as f:
		reader = csv.DictReader(f, delimiter='\t')

		for row in reader:
			# the files contain two tables, once we reach the second one, bail
			if row['Start Date'] == 'Total_Rows' : break

			titleKey = row['Title']
			if not titleKey in products : products[titleKey] = dict()
			title = products[titleKey]

			countryKey = row['Partner Share Currency']
			if not countryKey in title : title[countryKey] = TransactionCollection()
			country = title[countryKey]

			country.count += int(row['Quantity'])
			country.sum += Decimal(row['Extended Partner Share'])

	with open(f'tmp/{date.year}-{date.month}.csv', newline='') as f:
		# this file helpfully starts with two lines of nonsense, skip those
		f.readline()
		f.readline()
		reader = csv.DictReader(f, delimiter=',')

		for row in reader :
			# grab the currency abbreviation in parenthesis at the end of the field
			x = re.search('\w+(?=\))', row['Territory (Currency)'])
			# this file also has noise at the end, bail if we reach it
			if x is None : break
			currencyKey = x.group()

			currencies[currencyKey].sum += Decimal(row['Earned'])
			currencies[currencyKey].count += Decimal(row['Units Sold'])
			currencies[currencyKey].paid += Decimal(row['Proceeds'])


	for currency, transactions in currencies.items() :
		print(f'{currency}\t{transactions.count}\t{transactions.sum}\t\t{transactions.paid}')

	for product, countries in products.items() :
		print(product)
		for country, transactions in countries.items() :
			print(f'{country}\t{transactions.count}\t{transactions.sum}')
