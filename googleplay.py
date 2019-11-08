import csv
from decimal import Decimal
import collections
from collections import defaultdict
import os
import urllib.request
import zipfile
import subprocess
import glob
from io import StringIO

class TransactionCollection :
	def __init__(self):
		self.sum = Decimal(0)
		self.count = int(0)


def get(config, dates) :
	print('Opening Google Storage Util...')

	data = []

	if not os.path.exists('tmp') :
		os.makedirs('tmp')

	for date in dates :
		print('Fetching data for {0}-{1}'.format(date.year, date.month))

		subprocess.call('python gsutil/gsutil.py cp gs://pubsite_prod_rev_{0}/earnings/earnings_{1}{2}*.zip tmp'.format(config['bucket_id'], date.year, date.month))

		print('\tExtrating data...')

		try :
			zippath = glob.glob(os.path.join('tmp', 'earnings_{0}{1}*.zip'.format(date.year, date.month)))[0]
		except IndexError :
			print('\tNo data found for {0}{1}'.format(date.year, date.month))
		else :

			z = zipfile.ZipFile(zippath)
			z.extractall('tmp')

			print('\tParsing CSV data...')

			csvpath = glob.glob(os.path.join('tmp', 'PlayApps_{0}{1}*.csv'.format(date.year, date.month)))[0]

			data.append(open(csvpath, encoding="utf8").read(),)

			print('\tDone!\n')

	return data

# takes a list of data, data is an array of csv strings per month
# dates is a list of year/month tuples

def parse(data, dates) :
	# output is a dictionary with the month as key and the generated report as value
	output = dict()

	for index, entry in enumerate(data) :
		output['{0}-{1}'.format(dates[index][0], dates[index][1])] = parseSingle(entry, dates[index])

	return output

def parseSingle(entry, date) :
	input_file = csv.DictReader(StringIO(entry))

	# a TransactionCollection holds two values, a sum and a counts
	# we keep a dictionary of these hashed on the transaction type,
	# ie one for "Charge", one for "Google fee" and so on
	overall = defaultdict(TransactionCollection)

	# we keep a second dictionary that stores this same data, but per product
	# this is stored "one level down" ie product->transaction type->sum/count
	products = dict()

	for row in input_file:
		# the dictionary is a defaultdict, so we can write to any key and it will
		# automatically populate that with default values if it's the first time
		key = row['Transaction Type']
		overall[key].sum += Decimal(row['Amount (Merchant Currency)'])
		overall[key].count += 1

		# this defaultdict trickery won't work here, so we need to check if a
		# key exists, if not we create it
		productKey = row['Product Title']
		product = products.get(productKey, defaultdict(TransactionCollection));
		product[key].sum += Decimal(row['Amount (Merchant Currency)'])
		product[key].count += 1

		# because of the key creation bit, we need to store the value too
		products[productKey] = product

	text = f'Sales report for Google Play Apps {date.year}-{date.month}\n\n'
	text += summarize(overall)

	# make a nice horizontal ruler
	text += '-' * 61 + '\n\n'

	# now, output per product data
	text += 'Per product:'
	for key, value in products.items():
		text += summarizeProduct(key, value)

	return text

def summarize(collection) :
	text = ''
	sum = Decimal(0)
	for key, value in collection.items() :
		text += f'{key.ljust(25)}{format_currency(value.sum)}'
		if key == 'Charge' :
			text += format_count(value.count).rjust(15)
		text += '\n'

		sum += value.sum

	return text + '\nSum'.format(key).ljust(25) + '{0}\n\n'.format(format_currency(sum))

def summarizeProduct(name, collection) :
	sum = Decimal(0)
	count = int(0)

	for key, value in collection.items() :
		if key == 'Charge' : count = value.count
		sum += value.sum

	return f'\n    {name.ljust(21)}{format_currency(sum)}{format_count(count)}'

def format_currency(value) :
	return '{:16,.2f} SEK'.format(value).replace(',', ' ')

def format_count(value) :
	return '{:10} units'.format(value)

def setup() :
	print('Downloading gsutil...')

	try:
		urllib.request.urlretrieve('http://storage.googleapis.com/pub/gsutil.zip', 'gsutil.zip')
	except IOError as e:
		print('Can\'t retrieve gsutil.zip: {0}'.format(e))
		return

	print('Extracting gsutil...')

	try:
		z = zipfile.ZipFile('gsutil.zip')
	except zipfile.error as e:
		print('Bad zipfile')
		return

	z.extractall('.')

	z.close()
	os.unlink('gsutil.zip')

	print('Downloaded gsutil')

	subprocess.call('python gsutil/gsutil.py config', shell=True)
