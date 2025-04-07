import pandas as pd
from reports.report import *


class ReportTitle(Report):

    @property
    def name(self) -> str:
        return 'title'
    
    def generate(self, months, platforms, df: pd.DataFrame) -> str:
        df = df.groupby(['title'])
        df = df.agg({
            'units': 'sum',
            'sek': 'sum',
        })

        df = df.sort_values(['title'], ascending=True)
        df = df.reset_index()

        df.loc['total']= df.sum(numeric_only = True)

        df['units'] = df['units'].map(lambda a: self.format_units(a))
        df['sek'] = df['sek'].map(lambda a: self.format_currency_decimals(a))

        print(df)

    def report_row(self, title, units, sek):
        if not isinstance(units, str):
            units = self.format_units(units)
        if not isinstance(sek, str):
            sek = self.format_currency_decimals(sek)

        return f'{title:<28}{units:>10}{sek:>20}\n'