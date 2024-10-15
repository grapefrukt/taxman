import pandas as pd
from reports.report import *


class ReportForTaxes(Report):

    @property
    def name(self) -> str:
        return 'taxes'
    
    def generate(self, months, platforms, df: pd.DataFrame) -> str:
        df = df.groupby(['platform', 'year', 'month', 'title'])
        df = df.agg({
            'units': 'sum',
            'sek': 'sum',
        })

        df = df.sort_values(['year', 'month', 'title'], ascending=True)
        df = df.reset_index()

        # figure out if this report has both google play pass and play store
        if self.has_double_google(platforms):
            platforms.remove('play-pass')
            platforms.remove('play-store')
            platforms.append('google')

        for platform in platforms:
            for month in months:
                report, units, sek = self.report(platform, month, df)
                self.write(month, platform, report)

    def modify_months(self, months, platforms):
        if self.has_double_google(platforms):
            print("report has both play pass and play store, prepending extra month!\n")
            months.insert(0, months[0].add_months(-1))
        return months

    def report(self, platform, month, df: pd.DataFrame, header:bool=True):
        if platform == 'google':
            return self.google(month, df)

        out = ''
        
        if header:
            out += f'sales report for {platform} {month}\n\n'
            out += 'PER TITLE (including charges, fees, taxes, and refunds):\n\n'

        df = df.loc[
            (df['platform'] == platform) &
            (df['year'] == month.year) &
            (df['month'] == month.month)
            ]

        # drop any columns we don't need
        df = df[['title', 'units', 'sek']]

        # calculate a sum for the numeric columns (units/sek)
        # turn that into a dataframe (it was a series)
        df_sum = df.sum(numeric_only=True)

        out += self.report_row('title', 'units', 'revenue')
        for index, row in df.iterrows():
            out += self.report_row(row['title'], row['units'], row['sek'])

        out += '\n'
        out += self.report_row('', df_sum['units'], df_sum['sek'])

        out += '\n'

        return out, df_sum['units'], df_sum['sek']

    def google(self, month, df: pd.DataFrame):
        offset_month = month.add_months(-1)

        out = ""
        out += f'sales report for play pass {offset_month} and play store {month}\n\n'

        ps_report, ps_units, ps_sek = self.report('play-store', month, df, header=False)
        pp_report, pp_units, pp_sek = self.report('play-pass', offset_month, df, header=False)

        out += f'{self.hr('play store')}{ps_report}\n'
        out += f'{self.hr('play pass')}{pp_report}\n'
        out += f'{self.hr('total')}'
        out += f'{self.report_row('', ps_units + pp_units, ps_sek + pp_sek)}\n'

        return out, ps_units + pp_units, ps_sek + pp_sek

    def has_double_google(self, platforms):
        return 'play-pass' in platforms and 'play-store' in platforms

    def hr(self, title):
        return f'- {title.upper()} {'-' * (55 - len(title))}\n'

    def report_row(self, title, units, sek):
        if not isinstance(units, str):
            units = self.format_units(units)
        if not isinstance(sek, str):
            sek = self.format_currency_decimals(sek)

        return f'{title:<28}{units:>10}{sek:>20}\n'