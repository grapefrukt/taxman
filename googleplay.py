
from __future__ import print_function

import csv
from decimal import Decimal
import collections
import os
import urllib
import zipfile
import subprocess
import glob
import StringIO

def get(bucket_id, dates) :
	print('Opening Google Storage Util...')

	newdates = []

	if not os.path.exists('tmp') :
		os.makedirs('tmp')

	for date in dates :
		year = date[0]
		month = date[1]

		print('Fetching data for {0}-{1}'.format(year, month))

		subprocess.call('python gsutil/gsutil.py cp gs://pubsite_prod_rev_{0}/earnings/earnings_{1}{2}*.zip tmp'.format(bucket_id, year, month))

		print('\tExtrating data...')

		try :
			zippath = glob.glob(os.path.join('tmp', 'earnings_{0}{1}*.zip'.format(year, month)))[0]
		except IndexError :
			print('\tNo data found for {0}{1}'.format(year, month))
		else :

			z = zipfile.ZipFile(zippath)
			z.extractall('tmp')

			print('\tParsing CSV data...')

			csvpath = glob.glob(os.path.join('tmp', 'PlayApps_{0}{1}*.csv'.format(year, month)))[0]

			newdates.append(date + (open(csvpath).read(),))

			print('\tDone!\n')

	return newdates

def parse(entries, dates) :

	output = dict()

	for entry in entries :
		input_file = csv.DictReader(StringIO.StringIO(entry[2]))

		count_taxed_sales = 0
		count_untaxed_sales = 0
		count_refunds = 0

		sum_taxed_sales = Decimal(0)
		sum_untaxed_sales = Decimal(0)
		sum_tax = Decimal(0)
		sum_fees = Decimal(0)
		sum_fee_refund = Decimal(0)
		sum_tax_refund = Decimal(0)
		sum_sales_refund = Decimal(0)

		for row in input_file:
			if row['Transaction Type'] == 'Charge' :
				count_taxed_sales += 1
				sum_taxed_sales +=  Decimal(row['Amount (Merchant Currency)'])
			elif row['Transaction Type'] == 'Google fee' :
				sum_fees +=  Decimal(row['Amount (Merchant Currency)'])
			elif row['Transaction Type'] == 'Tax' :
				sum_tax +=  Decimal(row['Amount (Merchant Currency)'])
			else :
				exit('Unknown field type: "{0}" in Google Play {1}-{2}'.format(row['Transaction Type'], entry[0], entry[1]))

		total_sum = sum_taxed_sales + sum_untaxed_sales + sum_tax + sum_fees + sum_tax_refund + sum_sales_refund + sum_fee_refund

		text = 'Sales report for Google Play Apps {0}-{1}\n\n'.format(entry[0], entry[1])

		text += 'Taxed sales        {0}{1}\n'.format(format_currency(sum_taxed_sales), format_count(count_taxed_sales))
		text += 'Tax                {0}\n'.format(format_currency(sum_tax))
		text += 'Untaxed sales      {0}{1}\n'.format(format_currency(sum_untaxed_sales), format_count(count_untaxed_sales))
		text += 'Google fees        {0}\n'.format(format_currency(sum_fees))
		text += 'Refunds            {0}{1}\n'.format(format_currency(sum_sales_refund), format_count(-count_refunds))
		text += 'Tax refunds        {0}\n'.format(format_currency(sum_tax_refund))
		text += 'Google fee refunds {0}\n'.format(format_currency(sum_fee_refund))
		text += 'Sum                {0}{1}\n'.format(format_currency(total_sum), format_count(count_taxed_sales + count_untaxed_sales - count_refunds))
		text += '\n'

		output['{0}-{1}'.format(entry[0], entry[1])] = text

	return output

def format_currency(value) :
	return '{:16,.2f} SEK'.format(value).replace(',', ' ')

def format_count(value) :
	return '{:10} units'.format(value)

def setup() :
	print('Downloading gsutil...')

	try:
		urllib.urlretrieve('http://storage.googleapis.com/pub/gsutil.zip', 'gsutil.zip')
	except IOError, e:
		print('Can\'t retrieve gsutil.zip')
		return

	print('Extracting gsutil...')

	try:
		z = zipfile.ZipFile('gsutil.zip')
	except zipfile.error, e:
		print('Bad zipfile')
		return

	z.extractall('.')

	z.close()
	os.unlink('gsutil.zip')

	print('Downloaded gsutil')

	subprocess.call('python gsutil/gsutil.py config', shell=True)
