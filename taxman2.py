import argparse
from datetime import datetime, timedelta
from taxmonth import TaxMonth

from platforms.nintendo import PlatformNintendo

class TaxMan:
	def __init__(self):
		self.parser = argparse.ArgumentParser(description="Parse start date, optional end date, optional months, and platforms")
		self.add_arguments()

	def add_arguments(self):
		# Add start date argument
		self.parser.add_argument('--start', help='Start date in YYYY-MM format (optional)')
		
		# Add optional end date argument
		self.parser.add_argument('--end', help='End date in YYYY-MM format (optional)')
		
		# Add optional months argument
		self.parser.add_argument('--months', type=int, help='Number of months (optional)')

		# Add platforms argument (multiple strings can be provided)
		self.parser.add_argument('--platforms', nargs='+', help='List of platforms (optional)')

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
		months = args.months if args.months else 1
		if months < 1 : months = 1

		if not start and not end:
			raise ValueError("You must supply either a start or end date.")
		elif start and end and months :
			raise ValueError("Months makes no sense when start and end date was supplied.")
		elif start and not end : 
			end = start.add_months(months - 1)
		elif end and not start : 
			start = end.add_months(-months + 1)

		if not start.equals(end) and not end.is_after(start) :
			raise ValueError("End date must be later than start date.")

		# Get the platforms (optional)
		platforms = args.platforms if args.platforms else []

		return start, end, months, platforms

if __name__ == "__main__":
	taxman = TaxMan()
	start, end, num_months, active_platforms = taxman.parse_args()

	months = TaxMonth.make_range(start, end)

	print(f"start:     {start}")
	print(f"end:       {end}")
	print(f"count:     {num_months}")
	print(f"months:    {', '.join(map(str, months))}")

	# Print active_platforms if provided
	if active_platforms:
		print(f"active_platforms: {', '.join(active_platforms)}")
	else:
		print(f"active_platforms: none")

	platforms = {
		'nintendo': PlatformNintendo()
	}


