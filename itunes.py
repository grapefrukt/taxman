from appstoreconnect import Api
from collections import defaultdict
from datetime import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from decimal import ROUND_HALF_UP
import csv
from utils import TransactionCollection
from utils import format_currency
from utils import format_count
import re


def get(config, dates):
    # download(config, dates)
    parse(dates)
    return {}


def filename(date):
    return f'tmp/itunes_{date.year}-{date.month}.csv'


def download(config, dates):
    print('Connecting to AppStore Connect API...')
    api = Api(config['key_id'], config['key_file'], config['issuer_id'])

    for date in dates:
        # make the actual date and the apple date, we pick a day in the middle
        # of the month to try and avoid any "rounding" issues
        actualDate = datetime(int(date.year), int(date.month), 15)
        # the apple date is offset by a quarter
        appleDate = actualDate + relativedelta(months=3)

        print(f'Getting data for {date.year}-{date.month}')
        print(f' ({appleDate.year}-{appleDate.month:02d} in Apple Time)')

        api.download_finance_reports(filters={
            'vendorNumber': config['vendor_id'],
            'reportDate': f'{appleDate.year}-{appleDate.month:02d}'},
            save_to=filename(date))


def parse(dates):
    for date in dates:
        parseSingle(date)


def parseSingle(date):
    # first, we parse the data we can get from the API
    # this contains sales (currency and count) per country and product
    # but is missing data of what exactly was paid
    # that file needs to be manually retrieved from app store connect

    # this dictionary is keyed on product title
    # each value is yet another dictionary, this time keyed per currency
    # (which can include many countries)
    # these then hold a TransactionCollection that stores count and sum
    products = dict()

    # we keep a second dictionary for data from the payouts csv
    # this stores the earned amount in the local currency, the unit count and
    # most importantly the actual payout amount
    payouts = defaultdict(TransactionCollection)

    with open(filename(date), newline='') as f:
        reader = csv.DictReader(f, delimiter='\t')

        for row in reader:
            # the files contain two tables, once we reach the second one, bail
            if row['Start Date'] == 'Total_Rows':
                break

            titleKey = row['Title']
            if titleKey not in products:
                products[titleKey] = dict()
            title = products[titleKey]

            countryKey = row['Partner Share Currency']
            if countryKey not in title:
                title[countryKey] = TransactionCollection()
            country = title[countryKey]

            country.count += int(row['Quantity'])
            country.sum += Decimal(row['Extended Partner Share'])

    with open(f'tmp/{date.year}-{date.month}.csv', newline='') as f:
        # this file helpfully starts with two lines of nonsense, skip those
        f.readline()
        f.readline()
        reader = csv.DictReader(f, delimiter=',')

        for row in reader:
            # grab the currency abbreviation in parenthesis at the end
            x = re.search(r'\w+(?=\))', row['Territory (Currency)'])

            # this file also has noise at the end, bail if we reach it
            if x is None:
                break

            currencyKey = x.group()
            payouts[currencyKey].sum += Decimal(row['Earned'])
            payouts[currencyKey].count += Decimal(row['Units Sold'])
            payouts[currencyKey].paid += Decimal(row['Proceeds'])

    # for each product, add a "_" currency that stores a summary of sales
    # in the payout currency
    for product, currencies in products.items():
        currencies['_'] = TransactionCollection()

    for product, currencies in products.items():
        for currency, transactions in currencies.items():

            # skip the summary in the currency iteration
            if currency == '_':
                continue

            # calculate this produts share out of the total in this currency
            shareFraction = transactions.sum / payouts[currency].sum
            sharePayoutCurrency = Decimal(shareFraction * payouts[currency].paid)
            sharePayoutCurrency = sharePayoutCurrency.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)

            currencies['_'].paid += sharePayoutCurrency
            currencies['_'].count += transactions.count

        XYZ = currencies['_']
        print(f'    {product.ljust(21)}{format_currency(XYZ.paid)}{format_count(XYZ.count)}')
        #print(f'\n    {name.ljust(21)}{format_currency(sum)}{format_count(count)}')
