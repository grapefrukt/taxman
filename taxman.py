import configparser
import googleplay
import googleplaypass
import itunes
import os.path
import argparse
from collections import defaultdict
from utils import TaxMonth

if not os.path.isfile('taxman.cfg'):
    exit('Error: Config file (taxman.cfg) missing, please create it')

parser = argparse.ArgumentParser(
    description='Retrieve and summarize sales data between dates.')
parser.add_argument(
    'start',
    help='The first month to retrieve in the format YYYYMM')
parser.add_argument(
    'end',
    help='The last month to retrieve in the format YYYYMM (optional)',
    nargs='?')

args = parser.parse_args()

# if no end month is supplied, use the start month
if args.end is None:
    args.end = args.start

dates = []

startyear = int(args.start[:4])
endyear = int(args.end[:4])

for year in range(startyear, endyear + 1):
    startmonth = 1
    endmonth = 12

    if year == startyear:
        startmonth = int(args.start[-2:])
    if year == endyear:
        endmonth = int(args.end[-2:])

    if startmonth < 1 or startmonth > 12:
        exit('Error: Starting month range invalid: ' + str(startmonth))

    if endmonth < 1 or endmonth > 12:
        exit('Error: End month range invalid: ' + str(endmonth))

    for month in range(startmonth, endmonth + 1):
        dates.append(TaxMonth(str(year), str(month).zfill(2)))

config = configparser.ConfigParser()
config.read('taxman.cfg')

outPath = config['output']['path'].rstrip('/\\')
if not os.path.exists(outPath):
    os.makedirs(outPath)

output = defaultdict(dict)

if config['appstore']['enabled'] == 'true':
    output['appstore'] = itunes.get(config['appstore'], dates)

if config['google']['enabled'] == 'true':
    output['googleplay'] = googleplay.get(config['google'], dates)

if config['google']['play_pass_enabled'] == 'true':
    output['googleplay-pass'] = googleplaypass.get(config['google'], dates, config['packages'])

for platform, platformData in output.items():
    platformPath = f'{outPath}/{platform}'
    if not os.path.exists(platformPath):
        os.makedirs(platformPath)

    for month, monthData in platformData.items():
        path = f'{platformPath}/{month}.txt'
        f = open(path, 'w+')
        f.write(monthData)
        f.close()

        if config['output']['verbose'] == 'true':
            print(monthData)
