import pandas as pd
from reports.report import *


class ReportForTaxes(Report):
    
    def generate(self, months, platforms, df: pd.DataFrame) -> str:
        df = df.groupby(['year', 'month', 'title'])
        df = df.agg({
            'units': 'sum',
            'sek': 'sum',
        })

        df = df.sort_values(['year', 'month', 'title'], ascending=True)

        df['sek'] = df.apply(lambda row: self.format_currency(row['sek']), axis=1)
        df['units'] = df.apply(lambda row: self.format_units(row['units']), axis=1)

        print(df)

        return months[0]