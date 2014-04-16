import ConfigParser
import itunes
import googleplay
import os.path
import argparse

if not os.path.isfile('taxman.cfg') : exit('Error: Config file (taxman.cfg) missing, please create it')

parser = argparse.ArgumentParser(description='Retrieve and summarize sales data between dates.')
parser.add_argument("start", help="The first month to retrieve in the format YYYYMM")
parser.add_argument("end", help="The last month to retrieve in the format YYYYMM (optional)", nargs='?')

args = parser.parse_args()

# if no end month is supplied, use the start month
if args.end == None : args.end = args.start

dates = []

startyear = int(args.start[:4])
endyear = int(args.end[:4])

for year in range(startyear, endyear + 1) :
	startmonth = 1
	endmonth = 12

	if year == startyear : startmonth = int(args.start[-2:])
	if year == endyear : endmonth = int(args.end[-2:])

	if startmonth < 1 or startmonth > 12 : exit('Error: Starting month range invalid: ' + str(startmonth))
	if endmonth < 1 or endmonth > 12 : exit('Error: End month range invalid: ' + str(endmonth))

	for month in range(startmonth, endmonth + 1) : dates.append((year, str(month).zfill(2)))

config = ConfigParser.ConfigParser()
config.read('taxman.cfg')

data = itunes.get(config.get('iTunes', 'username'), config.get('iTunes', 'password'), dates)
if data : print itunes.parse(data)

if not os.path.isfile('gsutil/gsutil.py') : googleplay.setup()

data = googleplay.get(config.get('Google Play', 'bucket_id'), dates)
if data : googleplay.parse(data)