from appstoreconnect import Api
from collections import defaultdict
from datetime import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import csv
from utils import TransactionCollection
from utils import format_currency
from utils import format_count
import re
import os.path


def get(config, dates):
    download(config, dates)
    return parse(config, dates)


def filename(date):
    return f'itunes_{date.year}-{date.month}.csv'


def download(config, dates):
    api = Api(config['key_id'], config['key_file'], config['issuer_id'])

    for date in dates:
        # make the actual date and the apple date, we pick a day in the middle
        # of the month to try and avoid any "rounding" issues
        actualDate = datetime(int(date.year), int(date.month), 15)
        # the apple date is offset by a quarter
        appleDate = actualDate + relativedelta(months=3)

        print(f'Getting data for {date.year}-{date.month}', end='')
        print(f' ({appleDate.year}-{appleDate.month:02d} in Apple Time)')

        outpath = 'tmp/' + filename(date)
        # skip this file if we have it already
        if os.path.exists(outpath):
            continue

        print('Connecting to AppStore Connect API...')
        api.download_finance_reports(filters={
            'vendorNumber': config['vendor_id'],
            'reportDate': f'{appleDate.year}-{appleDate.month:02d}'},
            save_to=outpath)


# takes a list of data, data is an array of csv strings per month
# dates is a list of year/month tuples
def parse(config, dates):
    # output is a dictionary with the month as key
    # and the generated report as value
    output = dict()

    for date in dates:
        key = date.year + '-' + date.month
        output[key] = parseSingle(config, date)

    return output


def parseSingle(config, date):
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

    # parse the data we got from the api
    with open('tmp/' + filename(date), newline='') as f:
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

    # parse the data that was manually downloaded
    report = config['proceeds_report_path'] + f'/{date.year}-{date.month}.csv'
    if not os.path.exists(report):
        print(f'no app store payout report found for {date.year}-{date.month}')
        print(f'you need to download this manually!')
        print(f'put in this folder: ' + config['proceeds_report_path'])
        exit()

    actualPayout = Decimal()

    with open(report, newline='') as f:
        # this file helpfully starts with two lines of nonsense, skip those
        f.readline()
        f.readline()
        reader = csv.DictReader(f, delimiter=',')

        # this field name changed in late 2019, so we need to try both
        currencyField = 'Territory (Currency)'
        if currencyField not in reader.fieldnames:
            currencyField = 'Country or Region (Currency)'

        for row in reader:
            # grab the currency abbreviation in parenthesis at the end
            x = re.search(r'\((\w{3})\)', row[currencyField])

            # this file also has noise at the end
            # this can mostly be ignored, but we do want the actual payout sum
            # just to confirm out math
            if x is None:
                # check the last field, if it has numbers, it's the payout
                lastField = row['Bank Account Currency']
                if re.match(r'\d', lastField) is not None:
                    # strip out anything that isn't a number or a period
                    stripped = re.sub(r'[^\d\.]', '', lastField)
                    # sometimes there's two payouts in one report, add instead
                    # of replacing the current payouts
                    actualPayout += Decimal(stripped)
                continue

            currencyKey = x.group(1)
            payouts[currencyKey].sum += Decimal(row['Earned'])
            payouts[currencyKey].count += Decimal(row['Units Sold'])
            payouts[currencyKey].paid += Decimal(row['Proceeds'])

    # for each product, add a "_" currency that stores a summary of sales
    # in the payout currency
    for product, currencies in products.items():
        currencies['_'] = TransactionCollection()

    text = f'Sales report for AppStore Connect {date.year}-{date.month}\n\n'
    text += 'PER PRODUCT (including charges, fees, taxes, and refunds):\n\n'

    calculatedPayout = Decimal()
    for product, currencies in products.items():
        for currency, transactions in currencies.items():

            # skip the summary in the currency iteration
            if currency == '_':
                continue

            # calculate this produts share out of the total in this currency
            # it's possible to not have any sales for a currency, so we need
            # to guard for a division by zero here
            fraction = 0
            if payouts[currency].sum > 0:
                fraction = transactions.sum / payouts[currency].sum

            sharePayoutCurrency = Decimal(fraction * payouts[currency].paid)
            currencies['_'].paid += sharePayoutCurrency
            currencies['_'].count += transactions.count

        calculatedPayout += currencies['_'].paid
        text += product.ljust(25)
        text += format_currency(currencies['_'].paid)
        text += format_count(currencies['_'].count) + '\n'

    text += '\n\n'
    text += 'Payout'.ljust(25) + format_currency(actualPayout)
    # text += '\nPayout'.ljust(25) + format_currency(calculatedPayout)

    return text
