import pandas as pd
from reports.report import *


class ReportTitle(Report):

    @property
    def name(self) -> str:
        return 'title summary'
    
    def generate(self, months, platforms, df: pd.DataFrame) -> str:
        df = df.groupby(['title', 'year', 'month', 'platform'])
        df = df.agg({
            'units': 'sum',
            'sek': 'sum',
        })

        df = df.sort_values(['title'], ascending=True)
        df = df.reset_index()

        print(df.to_csv())

        #df_titles = df['title'].unique()
        #for title in df_titles:
        #    print(self.report(title, df))

    def report(self, title, df: pd.DataFrame):
        out = ''
        
        out += f'sales report for {title}\n\n'

        df = df.loc[(df['title'] == title)]

        # drop any columns we don't need
        df = df[['platform', 'units', 'sek']]

        # calculate a sum for the numeric columns (units/sek)
        # turn that into a dataframe (it was a series)
        df_sum = df.sum(numeric_only=True)

        out += self.report_row('title', 'units', 'revenue')
        for index, row in df.iterrows():
            out += self.report_row(row['platform'], row['units'], row['sek'])

        out += '\n'
        out += self.report_row('', df_sum['units'], df_sum['sek'])

        out += '\n'

        return out

    def hr(self, title):
        return f'- {title.upper()} {'-' * (55 - len(title))}\n'

    def report_row(self, title, units, sek):
        if not isinstance(units, str):
            units = self.format_units(units)
        if not isinstance(sek, str):
            sek = self.format_currency_decimals(sek)

        return f'{title:<28}{units:>10}{sek:>20}\n'