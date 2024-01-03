import csv
import datetime
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
import pandas


def get(config, dates):
    print(f'Google Play')

    data = []

    if not os.path.exists('tmp'):
        os.makedirs('tmp')

    for date in dates:
        filename = f'tmp/{date.year}{date.month}.csv'

        if not os.path.exists(filename):
            print('\tFetching data from Google...')
            download(config, date, 'earnings')


        paths = glob.glob(os.path.join('tmp', f'earnings{date.year}{date.month}*.csv'))
        
        print(f'\tParsing data for {date.year}-{date.month} ({len(paths)} files)... ')

        # combine all files in the list
        combined_csv = pandas.concat([pandas.read_csv(f) for f in paths ])
        # export to csv
        combined_path = os.path.join('tmp', f'{date.year}{date.month}.csv')
        combined_csv.to_csv(combined_path, index=False, encoding='utf-8')

        data.append(open(combined_path, encoding="utf8").read())

    return parse(data, dates)


def download(config, date, path):
    print(f'Fetching data for {date.year}-{date.month}')
    url = f'gs://pubsite_prod_rev_{config.get("bucket_id")}'
    url += f'/{path}/{path}_{date.year}{date.month}*.zip'
    print(f'"{config.get("gcloud_path")}" storage cp {url} tmp')
    subprocess.call(f'"{config.get("gcloud_path")}" storage cp {url} tmp')

    print('\tExtracting data...')

    try:
        # a single month may have more than one zip, just to make our life harder
        # we use a wildcard to match them all here
        zippaths = glob.glob(
            os.path.join('tmp', f'{path}_{date.year}{date.month}*.zip')
        )
    except IndexError:
        print(f'\t⚠️ No data found for {date.year}{date.month}')
        return False
    else:
        # iterate over all files in the zip, extracting them one by one
        # i have never seen a report have more than one file in its zip,
        # but this gives us access to the file name of the file we're extracting
        # we need this so we can rename it immediately after extracting
        
        # this is needed because when a report comes in multiple zips, the contained csv's
        # will have the SAME name, meaning they'll overwrite eachother!

        for idx, zippath in enumerate(zippaths) :
            with zipfile.ZipFile(zippath, 'r') as zfile :
                filenames = zfile.namelist()
                for filename in filenames :
                    zfile.extract(filename, 'tmp')
                    oldname = os.path.join('tmp', filename)
                    newname = os.path.join('tmp', f'{path}{date.year}{date.month}-{idx}.csv')
                    # remove the new file if it exists, as to not cause errors
                    if os.path.exists(newname) : os.remove(newname)
                    os.rename(oldname, newname)
        return True


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
        timestamp = datetime.datetime.strptime(row['Transaction Date'], '%b %d, %Y').date()
        # the date tuple here has the month as a string with a leading zero, the timestamp does not, hence the int-cast
        if int(timestamp.month) != int(date.month) and timestamp.year != date.year :
            print(f'⚠️ transaction in wrong month! expected: {date.year}-{date.month} got: {timestamp.year}-{timestamp.month}')
            continue

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
        # tax line is like a product, but has an empty key, skip it
        if key == '': continue
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
        if key == 'Charge' or key == 'Charge refund':
            text += format_count(value.count).rjust(15)
        text += '\n'
        sum += value.sum
    return text


def summarizeProduct(name, collection):
    sum = Decimal(0)
    count = int(0)

    for key, value in collection.items():
        if key == 'Charge':
            count += value.count
        elif key == 'Charge refund':
            count -= value.count
        sum += value.sum

    return f'{name.ljust(25)}{format_currency(sum)}{format_count(count)}\n'


def setup():
    print('Downloading gsutil...')

    try:
        urllib.request.urlretrieve(
            'http://storage.googleapis.com/pub/gsutil.zip',
            'gsutil.zip')
    except IOError as e:
        print('⚠️ Can\'t retrieve gsutil.zip: {0}'.format(e))
        return

    print('Extracting gsutil...')

    try:
        z = zipfile.ZipFile('gsutil.zip')
    except zipfile.error:
        print('⚠️ Bad zipfile')
        return

    z.extractall('.')

    z.close()
    os.unlink('gsutil.zip')

    print('Downloaded gsutil')

    subprocess.call('python gsutil/gsutil.py config', shell=True)
