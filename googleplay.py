
from __future__ import print_function

import csv
from decimal import Decimal
import locale
import os
import sys
import platform
import urllib
import zipfile
import subprocess
import glob
import shutil
import StringIO
import re

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

def parse(entries) : 
	for entry in entries :
		input_file = csv.DictReader(StringIO.StringIO(entry[2]))

		transactions = {};

		for row in input_file:
			key = row['Description']
			if key not in transactions:
				transactions[key] = {'Charge' : Decimal(0), 'Google fee' : Decimal(0), 'Tax' : Decimal(0), 'Tax refund' : Decimal(0), 'Charge refund' : Decimal(0), 'Google fee refund' : Decimal(0)}

			transactions[key][row['Transaction Type']] += Decimal(row['Amount (Merchant Currency)'])

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

		for key, row in transactions.iteritems() :
			if row['Tax'] > 0 :
				sum_taxed_sales += row['Charge']
				sum_tax += row['Tax']
				count_taxed_sales += 1
			else :
				sum_untaxed_sales += row['Charge']
				count_untaxed_sales += 1

			sum_fees += row['Google fee']
			sum_fee_refund += row['Google fee refund']
			sum_sales_refund += row['Charge refund']
			sum_tax_refund += row['Tax refund']

			if row['Google fee refund'] > 0 :
				count_refunds += 1

		total_sum = sum_taxed_sales + sum_untaxed_sales + sum_tax + sum_fees + sum_tax_refund + sum_sales_refund + sum_fee_refund

		output = 'Sales report for Google Play Apps {0}-{1}\n\n'.format(entry[0], entry[1])

		output += 'Taxed sales        {0}{1}\n'.format(format_currency(sum_taxed_sales), format_count(count_taxed_sales))
		output += 'Tax                {0}\n'.format(format_currency(sum_tax))
		output += 'Untaxed sales      {0}{1}\n'.format(format_currency(sum_untaxed_sales), format_count(count_untaxed_sales))
		output += 'Google fees        {0}\n'.format(format_currency(sum_fees))
		output += 'Refunds            {0}{1}\n'.format(format_currency(sum_sales_refund), format_count(-count_refunds))
		output += 'Tax refunds        {0}\n'.format(format_currency(sum_tax_refund))
		output += 'Google fee refunds {0}\n'.format(format_currency(sum_fee_refund))
		output += 'Sum                {0}{1}\n'.format(format_currency(total_sum), format_count(count_taxed_sales + count_untaxed_sales - count_refunds))
		output += '\n'

		print(output)

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