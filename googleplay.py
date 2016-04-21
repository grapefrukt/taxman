
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

		sums = collections.defaultdict(Decimal)
		counts = collections.defaultdict(int)

		for row in input_file:
			sums[row['Transaction Type']] += Decimal(row['Amount (Merchant Currency)'])
			counts[row['Transaction Type']] += 1

		text = 'Sales report for Google Play Apps {0}-{1}\n\n'.format(entry[0], entry[1])

		total_sum = Decimal(0)

		for key, value in sums.items():
			text += '{0}'.format(key).ljust(25) + '{0}'.format(format_currency(value))
			if key == 'Charge' : 
				text += '{0}'.format(format_count(counts[key])).rjust(15)
			text += '\n'

			total_sum += value

		text += '\nSum'.format(key).ljust(25) + '{0}\n'.format(format_currency(total_sum))

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
		print('Can\'t retrieve gsutil.zip: {0}'.format(e))
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
