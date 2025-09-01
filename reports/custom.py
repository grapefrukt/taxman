import pandas as pd
from reports.report import *


class ReportCustom(Report):

    @property
    def name(self) -> str:
        return 'custom'
    
    def generate(self, months, platforms, df: pd.DataFrame):
        pd.set_option('future.no_silent_downcasting', True)

        df = df.groupby(self.arguments)
        df = df.agg({
            'units': 'sum',
            'sek': 'sum',
        })

        df = df.sort_values(self.arguments, ascending=True)
        df = df.reset_index()

        df.loc['total'] = df.sum(numeric_only = True)
        df.loc['total'] = df.loc['total'].fillna('')
        
        df['units'] = df['units'].map(lambda a: self.format_units(a))
        df['sek'] = df['sek'].map(lambda a: self.format_currency_decimals(a))

        print(df)

        self.write(f'custom report for {months[0]} to {months[-1]}, {self.arguments}', '', df.to_csv())