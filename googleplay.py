
from __future__ import print_function

import csv
from decimal import Decimal
import locale
import os
import sys
import platform
import urllib
import zipfile

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