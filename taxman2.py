import argparse
from datetime import datetime, timedelta
from taxmonth import TaxMonth

class TaxMan:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="Parse start date, optional end date, optional months, and platforms")
        self.add_arguments()

    def add_arguments(self):
        # Add start date argument (required)
        self.parser.add_argument('start_date', help='Start date in YYYY-MM format')
        
        # Add optional end date argument
        self.parser.add_argument('--end_date', help='End date in YYYY-MM format (optional)')
        
        # Add optional months argument
        self.parser.add_argument('--months', type=int, help='Number of months (optional)')

        # Add platforms argument (multiple strings can be provided)
        self.parser.add_argument('--platforms', nargs='+', help='List of platforms (optional)')

    def parse_args(self):
        args = self.parser.parse_args()

        # Parse and validate the start date
        start_date = TaxMonth.from_string(args.start_date)
        if not start_date:
            raise ValueError("Invalid start date format. Use YYYY-MM.")

        # Parse and validate the end date (optional)
        if args.end_date:
            end_date = self.parse_date(args.end_date)
            if not end_date:
                raise ValueError("Invalid end date format. Use YYYY-MM.")
        else:
            end_date = start_date  # Default end date to start date if not provided

        # Parse months (optional)
        months = args.months if args.months else 0

        # Get the platforms (optional)
        platforms = args.platforms if args.platforms else []

        return start_date, end_date, months, platforms


# Example usage
if __name__ == "__main__":
    taxman = TaxMan()
    start_date, end_date, months, platforms = taxman.parse_args()

    # If months are provided, calculate the end date by adding months
    if months:
        calculated_end_date = start_date.add_months(months)
        print(f"Start Date: {start_date}")
        print(f"End Date calculated with {months} months: {calculated_end_date}")
    else:
        print(f"Start Date: {start_date}")
        print(f"End Date: {end_date}")

    # Print platforms if provided
    if platforms:
        print(f"Platforms: {', '.join(platforms)}")
    else:
        print("No platforms specified.")
