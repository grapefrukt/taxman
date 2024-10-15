import argparse
import multiprocessing as mp
import yaml

from taxmonth import TaxMonth
from platforms.platform import *
from platforms.appstore import PlatformAppStore
from platforms.nintendo import PlatformNintendo
from platforms.playpass import PlatformPlayPass
from platforms.playstore import PlatformPlayStore
from platforms.steam import PlatformSteam

from reports.report import *
from reports.taxes import ReportForTaxes 

class TaxMan:

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog='taxman',
            description="Gets sales data from start date up to end date for specified platforms")
        self.parser.add_argument(
            '--start', '--from', help='Start date in YYYY-MM format (optional)')
        self.parser.add_argument(
            '--end', '--to', help='End date in YYYY-MM format (optional)')
        self.parser.add_argument(
            '--months', '--count', type=int, help='Number of months (optional)')
        self.parser.add_argument(
            '--platforms', '--platform', nargs='+', help='List of platforms')
        self.parser.add_argument(
            '--report', nargs='?', help='Report type to generate', default="taxes")
        self.parser.add_argument(
            '--download', help='Download sales data if missing', default=False)

    def intialize(self):
        args = self.parser.parse_args()

        # Parse and validate the start date
        start = None
        if args.start:
            start = TaxMonth.from_string(args.start)
            if not start:
                raise ValueError('Invalid start date format. Use YYYY-MM.')

        # Parse and validate the end date (optional)
        end = None
        if args.end:
            end = TaxMonth.from_string(args.end)
            if not end:
                raise ValueError('Invalid end date format. Use YYYY-MM.')

        # Parse months
        has_months = args.months
        months = args.months if has_months else 1
        if months < 1:
            months = 1

        if not start and not end:
            raise ValueError('You must supply a date (YYYY-MM) in either --start or --end (or both)')
        elif start and end and has_months:
            raise ValueError(
                '--months makes no sense when start and end date was supplied.')
        elif start and not end:
            end = start.add_months(months - 1)
        elif end and not start:
            start = end.add_months(-months + 1)

        if not start.equals(end) and not end.is_after(start):
            raise ValueError('End date must be later than start date.')

        # read the config file
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)

        if not args.platforms:
            raise ValueError('You must supply at least one --platform')

        # Get the platforms and create the corresponding classes
        platforms = []
        for platform in args.platforms:
            match platform:
                case 'nintendo':
                    platforms.append(PlatformNintendo(config)),
                case 'play-pass':
                    platforms.append(PlatformPlayPass(config)),
                case 'play-store':
                    platforms.append(PlatformPlayStore(config)),
                case 'appstore':
                    platforms.append(PlatformAppStore(config)),
                case 'steam':
                    platforms.append(PlatformSteam(config)),
                case _:
                    raise ValueError(f'Unknown platform: {platform}')

        report = None
        match args.report:
            case 'taxes':
                report = ReportForTaxes(config)
            case _:
                raise ValueError(f'Unknown report: {report}')

        return download, TaxMonth.make_range(start, end), platforms, report


def parse(arg):
    platform, month = arg
    result, month_df = platform.parse(month)
    match result:
        case ParseResult.OK:
            print(f'{platform.name} parsed {month} ok')
            month_df['platform'] = platform.name
            month_df['month'] = month.month
            month_df['year'] = month.year
            return month_df
        case ParseResult.EXCLUDED:
            print(f'{platform.name} excluded {month}')
        case ParseResult.MISSING:
            print(f'{platform.name} is missing {month}, expected at: {platform.month_to_path(month)}')


if __name__ == "__main__":
    taxman = TaxMan()
    download, months, platforms, report = (False, [], [], None)
    try:
        download, months, platforms, report = taxman.intialize()
    except Exception as e:
        print(e)
        exit()

    print(f"platforms:   {', '.join(map(str, platforms))}")
    print(f"download:    {str(download).lower()}")
    print(f"start:       {months[0]}")
    print(f"end:         {months[-1]}")
    print(f"month count: {len(months)}")

    # make a list of the platforms as plain strings
    platforms_str = [str(p) for p in platforms]

    requested_months = months
    months = report.modify_months(months, platforms_str)

    if download:
        jobs_download = []
        for platform in platforms:
            for month in months:
                result = jobs_download.append((platform, month))
        with mp.Pool(processes=4) as pool:
            results = pool.map(parse, jobs_download)

    jobs_parse = []
    for platform in platforms:
        for month in months:
            jobs_parse.append((platform, month))
    with mp.Pool(processes=4) as pool:
        results = pool.map(parse, jobs_parse)
    df = pd.concat(results)

    if len(df.index) == 0:
        exit('no rows in dataframe')



    report.generate(requested_months, platforms_str, df)