import configparser
import googleplay
import googleplaypass
import itunes
import os.path
from os.path import exists as file_exists
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
    output['app store'] = itunes.get(config['appstore'], dates)

if config['google']['enabled'] == 'true':
    output['google play store'] = googleplay.get(config['google'], dates)

if config['google']['play_pass_enabled'] == 'true':
    output['google play pass'] = googleplaypass.get(config['google'], dates, config['packages'])

if config['google']['enabled'] == 'true' and config['google']['play_pass_enabled'] == 'true':
    output['google play'] = googleplaypass.merge(output['google play store'], output['google play pass'])
    del output['google play store']
    del output['google play pass']

for platform, platformData in output.items():
    platformPath = f'{outPath}/{platform}'
    if not os.path.exists(platformPath):
        os.makedirs(platformPath)

    for month, monthData in platformData.items():
        path = f'{platformPath}/{month}.txt'

        # to make things easier below, we create the output file here, if it does not already exist
        if not file_exists(path): 
            with open(path, 'x') as f:
                f.write('')

        # then we can open it in read+ mode, which allows us to also write if we need to
        # there is no mode that will do this AND create the file if it doesn't exist
        with open(path, 'r+') as f:
            old_report = f.read()

            if config['output']['overwrite'] == 'false' and old_report != monthData and old_report != "" : 
                print(f'{path} was already generated and is different from generated report, will not overwrite')
            elif config['output']['overwrite'] == 'false' and old_report == monthData : 
                # generated report was same as already present report, do nothing
                print(f'{path} was already generated and is identical to generated report')
            else :
                # seek to beginning of file again (because we read)
                f.seek(0)
                f.write(monthData)
                # finally truncate, should this new report be shorter
                f.truncate()
                print(f'{path} written')

        if config['output']['verbose'] == 'true':
            print(monthData)
