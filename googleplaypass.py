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

from googleplay import download


def get(config, dates, packagemap):
    print(f'Google Play Pass')

    data = []

    if not os.path.exists('tmp'):
        os.makedirs('tmp')

    for date in dates:
        filename = f'tmp/play_pass_earnings_{date.year}{date.month}.csv'

        if not os.path.exists(filename):
            print('\tFetching data from Google...')
            download(config, date, 'play_pass_earnings')

        print(f'\tParsing data for {date.year}-{date.month}... ', end='')
        data.append(open(filename, encoding="utf8").read(),)
        print('done!')

    return parse(data, dates, packagemap)


# takes a list of data, data is an array of csv strings per month
# dates is a list of year/month tuples
def parse(data, dates, packagemap):
    # output is a dictionary with the month as key
    # and the generated report as value
    output = dict()

    for index, entry in enumerate(data):
        key = dates[index].year + '-' + dates[index].month
        output[key] = parseSingle(entry, dates[index], packagemap)

    return output


def parseSingle(entry, date, packagemap):
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
        productKey = row['Product Id']
        if productKey not in products:
            products[productKey] = defaultdict(TransactionCollection)
        product = products[productKey]
        product[key].sum += Decimal(row['Amount (Merchant Currency)'])
        product[key].count += 1

    text = f'Revenue report for Google Play Pass {date.year}-{date.month}\n\n'

    text += summarize(overall)

    # output per product data
    text += '\n\n'
    text += 'PER PRODUCT (including charges, fees, taxes, and refunds):\n\n'
    for key, value in products.items():
        name = packagemap.get(key, fallback=key);
        text += summarizeProduct(name, value)

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

    return f'{name.ljust(25)}{format_currency(sum)}\n'