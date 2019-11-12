import csv
from utils import TransactionCollection
from utils import format_currency
from utils import format_count
from decimal import Decimal
from collections import defaultdict
import os
import urllib.request
import zipfile
import subprocess
import glob
from io import StringIO
import os.path


def get(config, dates):
    data = []

    if not os.path.exists('tmp'):
        os.makedirs('tmp')

    for date in dates:
        filename = f'tmp/PlayApps_{date.year}{date.month}.csv'

        if not os.path.exists(filename):
            download(config, date)

        print('\tParsing CSV data...')
        data.append(open(filename, encoding="utf8").read(),)
        print('\tDone!\n')

    return parse(data, dates)


def download(config, date):
    print(f'Fetching data for {date.year}-{date.month}')
    url = f'gs://pubsite_prod_rev_{config.get("bucket_id")}'
    url += f'/earnings/earnings_{date.year}{date.month}*.zip'
    subprocess.call(f'python gsutil/gsutil.py cp {url} tmp')

    print('\tExtrating data...')

    try:
        zippath = glob.glob(
            os.path.join('tmp', f'earnings_{date.year}{date.month}*.zip')
        )[0]
    except IndexError:
        print('\tNo data found for {0}{1}'.format(date.year, date.month))
    else:
        z = zipfile.ZipFile(zippath)
        z.extractall('tmp')


# takes a list of data, data is an array of csv strings per month
# dates is a list of year/month tuples
def parse(data, dates):
    # output is a dictionary with the month as key
    # and the generated report as value
    output = dict()

    for index, entry in enumerate(data):
        key = dates[index].year + '-' + dates[index].month
        output[key] = parseSingle(entry, dates[index])

    return output


def parseSingle(entry, date):
    input_file = csv.DictReader(StringIO(entry))

    # a TransactionCollection holds two values, a sum and a counts
    # we keep a dictionary of these hashed on the transaction type,
    # ie one for "Charge", one for "Google fee" and so on
    overall = defaultdict(TransactionCollection)

    # we keep a second dictionary that stores this same data, but per product
    # this is stored "one level down" ie product->transaction type->sum/count
    products = dict(defaultdict(TransactionCollection))

    for row in input_file:
        # the dictionary is a defaultdict, so we can write to any key and it
        # will automatically populate that with default values if it's the
        # first time
        key = row['Transaction Type']
        overall[key].sum += Decimal(row['Amount (Merchant Currency)'])
        overall[key].count += 1

        # this defaultdict trickery won't work here, so we need to check if a
        # key exists, if not we create it
        productKey = row['Product Title']
        if productKey not in products:
            products[productKey] = defaultdict(TransactionCollection)
        product = products[productKey]
        product[key].sum += Decimal(row['Amount (Merchant Currency)'])
        product[key].count += 1

    text = f'Sales report for Google Play Apps {date.year}-{date.month}\n\n'

    text += 'CHARGES, FEES, TAXES, AND REFUNDS:\n\n'
    text += summarize(overall)

    # output per product data
    text += '\n\n'
    text += 'PER PRODUCT (including charges, fees, taxes, and refunds):\n\n'
    for key, value in products.items():
        text += summarizeProduct(key, value)

    text += '\n\n'
    text += summarizePayout(overall)

    return text


def summarizePayout(collection):
    sum = Decimal(0)
    for key, value in collection.items():
        sum += value.sum
    return 'Payout'.ljust(25) + f'{format_currency(sum)}'


def summarize(collection):
    text = ''
    sum = Decimal(0)
    for key, value in collection.items():
        text += f'{key.ljust(25)}{format_currency(value.sum)}'
        if key == 'Charge':
            text += format_count(value.count).rjust(15)
        text += '\n'
        sum += value.sum
    return text


def summarizeProduct(name, collection):
    sum = Decimal(0)
    count = int(0)

    for key, value in collection.items():
        if key == 'Charge':
            count = value.count
        sum += value.sum

    return f'{name.ljust(25)}{format_currency(sum)}{format_count(count)}\n'


def setup():
    print('Downloading gsutil...')

    try:
        urllib.request.urlretrieve(
            'http://storage.googleapis.com/pub/gsutil.zip',
            'gsutil.zip')
    except IOError as e:
        print('Can\'t retrieve gsutil.zip: {0}'.format(e))
        return

    print('Extracting gsutil...')

    try:
        z = zipfile.ZipFile('gsutil.zip')
    except zipfile.error:
        print('Bad zipfile')
        return

    z.extractall('.')

    z.close()
    os.unlink('gsutil.zip')

    print('Downloaded gsutil')

    subprocess.call('python gsutil/gsutil.py config', shell=True)
