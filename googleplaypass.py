import csv
from utils import TransactionCollection
from utils import format_currency
from decimal import Decimal
from collections import defaultdict
import os
from io import StringIO
import os.path
from googleplay import download
import re
from utils import TaxMonth

merge_spacer = '\n\n--------------------------------------------------------------\n\n'


def get(config, dates, packagemap):
    print('Google Play Pass')

    data = []

    if not os.path.exists('tmp'):
        os.makedirs('tmp')

    for date in dates:
        filename = f'tmp/play_pass_earnings{date.year}{date.month}-0.csv'
        file_exists = os.path.exists(filename)

        if not file_exists:
            print('\tFetching data from Google...')
            file_exists = download(config, date, 'play_pass_earnings')

        if not file_exists:
            print(f'\tNo data for {date.year}-{date.month}, returning empty')
            return dict()

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

    text = 'Revenue report for Google Play Pass '
    text += f'{date.year}-{date.month}\n\n'

    text += summarize(overall)

    # output per product data
    text += '\n\n'
    text += 'PER PRODUCT (including charges, fees, taxes, and refunds):\n\n'
    for key, value in products.items():
        name = packagemap.get(key, fallback=key)
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
    for key, value in collection.items():
        sum += value.sum

    return f'{name.ljust(25)}{format_currency(sum)}\n'


def adjustTaxMonth(date, month_delta):
    year = int(date.year)
    month = int(date.month) + month_delta

    while month < 1:
        year -= 1
        month += 12

    while month > 12:
        year += 1
        month -= 12

    return TaxMonth(str(year), str(month).zfill(2))


def parseTaxMonth(str):
    return TaxMonth(str[0:4], str[5:7])


def merge(playstore, playpass):
    # output is a dictionary with the month as key
    # and the generated report as value
    output = dict()

    for month, monthData in playstore.items():
        pay_date = parseTaxMonth(month)
        pay_date = adjustTaxMonth(pay_date, +1)

        output[month] = 'Report for Google Play as paid on '
        output[month] += f'{pay_date.year}-{pay_date.month}\n\n'

        output[month] += monthData + merge_spacer

    for month, monthData in playpass.items():
        pass_date = parseTaxMonth(month)
        pass_date = adjustTaxMonth(pass_date, +1)
        if pass_date.key() not in output:
            continue
        output[pass_date.key()] += monthData

    for month, monthData in output.items():
        # parse any lines that say Payout
        payouts = re.findall(r'Payout\W+([\d ,]+) ', monthData)
        sum = Decimal(0)
        for payout in payouts:
            stripped = payout.replace(',', '.').replace(' ', '')
            decimal = Decimal(stripped)
            sum += decimal

        output[month] += merge_spacer + 'Total Payout:'.ljust(25) + f'{format_currency(sum)}\n'

    return output
