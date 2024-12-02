import pandas as pd
from reports.report import *


class ReportPlatform(Report):

    @property
    def name(self) -> str:
        return 'platform summary'
    
    def generate(self, months, platforms, df: pd.DataFrame) -> str:
        df = df.groupby(['platform', 'year', 'month', 'title'])
        df = df.agg({
            'units': 'sum',
            'sek': 'sum',
        })

        df = df.sort_values(['year', 'month', 'title'], ascending=True)
        df = df.reset_index()

        print(df)

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

    def hr(self, title):
        return f'- {title.upper()} {'-' * (55 - len(title))}\n'

    def report_row(self, title, units, sek):
        if not isinstance(units, str):
            units = self.format_units(units)
        if not isinstance(sek, str):
            sek = self.format_currency_decimals(sek)

        return f'{title:<28}{units:>10}{sek:>20}\n'