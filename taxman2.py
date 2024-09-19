import argparse
import yaml

from datetime import datetime, timedelta
from taxmonth import TaxMonth

from platforms.platform import *
from platforms.appstore import PlatformAppStore
from platforms.nintendo import PlatformNintendo
from platforms.playpass import PlatformPlayPass
from platforms.playstore import PlatformPlayStore
from platforms.steam import PlatformSteam

class TaxMan:
	def __init__(self):
		self.parser = argparse.ArgumentParser(description="Gets sales data from start date up to end date for specified platforms")
		self.add_arguments()

	def add_arguments(self):
		# Add start date argument
		self.parser.add_argument('--start', '--from', help='Start date in YYYY-MM format (optional)')
		
		# Add optional end date argument
		self.parser.add_argument('--end', '--to', help='End date in YYYY-MM format (optional)')
		
		# Add optional months argument
		self.parser.add_argument('--months', '--count', type=int, help='Number of months (optional)')

		# Add platforms argument (multiple strings can be provided)
		self.parser.add_argument('--platforms', '--platform', nargs='+', help='List of platforms (optional)')

	def parse_args(self):
		args = self.parser.parse_args()

		# Parse and validate the start date
		start = None
		if args.start: 
			start = TaxMonth.from_string(args.start)
			if not start:
				raise ValueError("Invalid start date format. Use YYYY-MM.")

		# Parse and validate the end date (optional)
		end = None
		if args.end:
			end = TaxMonth.from_string(args.end)
			if not end:
				raise ValueError("Invalid end date format. Use YYYY-MM.")
		
		# Parse months
		has_months = args.months
		months =  args.months if has_months else 1
		if months < 1 : months = 1

		if not start and not end:
			raise ValueError("You must supply either a start or end date.")
		elif start and end and has_months :
			raise ValueError("Months makes no sense when start and end date was supplied.")
		elif start and not end : 
			end = start.add_months(months - 1)
		elif end and not start : 
			start = end.add_months(-months + 1)

		if not start.equals(end) and not end.is_after(start) :
			raise ValueError("End date must be later than start date.")

		# Get the platforms (optional)
		platforms = args.platforms if args.platforms else []

		return TaxMonth.make_range(start, end), platforms

if __name__ == "__main__":
	taxman = TaxMan()
	months, active_platforms = taxman.parse_args()

	print(f"start:     {months[0]}")
	print(f"end:       {months[-1]}")
	print(f"count:     {len(months)}")
	print(f"months:    {', '.join(map(str, months))}")

	with open('config.yaml', 'r') as file:
	    config = yaml.safe_load(file)

	print(config['data_path'])

	# Print active_platforms if provided
	if active_platforms:
		print(f"active_platforms: {', '.join(active_platforms)}")
	else:
		print(f"active_platforms: none")

	platforms = {
		'nintendo'  : PlatformNintendo(config),
		'play-pass' : PlatformPlayPass(config),
		'play-store': PlatformPlayStore(config),
		'appstore'  : PlatformAppStore(config),
		'steam'     : PlatformSteam(config),
	}

	for platform in active_platforms:
		if platform not in platforms: 
			raise ValueError(f'Unknown platform: {platform}')

	df = pd.DataFrame()

	for key, platform in platforms.items():
		if key not in active_platforms: continue
		for month in months:
			result = platform.parse(month)
			match result[0]:
				case ParseResult.OK:
					print(f'{platform.name} parsed {month} ok')
					# tag this data with the platform it came from
					result[1]['platform'] = platform.name
					# then concat it to our big data table
					df = pd.concat([df, result[1]])
				case ParseResult.EXCLUDED:
					print(f'{platform.name} exluded {month}')
				case ParseResult.MISSING:
					print(f'{platform.name} is missing {month}, expected at: {platform.month_to_path(month)}')

	#df = df.groupby(['title', 'month'])
	#df = df.agg({
	#	'units':'sum', 
	#	'sek':'sum',
	#	'platform': 'first',
	#})
	#df = df.reset_index()
	#df = df.sort_values(by=['month', 'title'])

	#df = df.groupby(['platform', 'title'])
	#df = df.agg({
	#	'units':'sum', 
	#	'sek':'sum',
	#})

	df = df.groupby(['platform', 'title'])
	df = df.agg({
		'units':'sum', 
		#'usd':'sum',
		'sek':'sum',
	})

	def format_currency(value) :
		return '{:16,.0f} SEK'.format(value).replace(',', ' ').replace('.', ',')

	def format_units(value):
		return '{:10,.0f}'.format(value).replace(',', ' ').replace('.', ',')

	df['sek'] = df.apply(lambda row: format_currency(row['sek']), axis=1)
	df['units'] = df.apply(lambda row: format_units(row['units']), axis=1)

	print(df)
