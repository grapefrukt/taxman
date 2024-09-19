import pandas as pd
from platforms.platform import *
import re


class PlatformSteam(Platform):
    @property
    def name(self) -> str:
        return 'steam'

    @property
    def data_extension(self) -> str:
        return '.htm'

    def download(self, month):
        pass

    def _parse(self, month):
        df = pd.read_html(self.month_to_path(month))
        df = df[0]

        # early 2014 steam did not have the multi index tables, so this special case is needed
        if isinstance(df.columns, pd.MultiIndex):
            # the table has multiple headers, this is annoying so we use this magic incantation to collapse them
            df.columns = df.columns.map('{0[1]}'.format)
        else:
            # we rename the column to match what all other multi header reports will have
            df = df.rename(columns={'Revenue Share': 'Total'})

        cols = ['Product (Id#)', 'Net Units Sold', 'Total']
        df = df.filter(cols)

        # rename some columns to better names
        df = df.rename(columns={
            'Product (Id#)': 'title',
            'Net Units Sold': 'units',
            'Total': 'usd',
        })

        # the table has a summary row at the end with some missing values, this drops all lines with missing values
        df = df.dropna()

        df['usd'] = df['usd'].apply(self.strip_dollar_sign)
        df['title'] = df['title'].apply(self.remove_package_id)

        # tag all rows with this month too
        df['month'] = month

        df['sek'] = df['usd'] * 9.0

        # print(df)

        # df2 = pd.read_csv(f'data/{self.name}/payments.csv', sep='\t')
        # print(df2)

        return ParseResult.OK, df

    def strip_dollar_sign(self, str) -> str:
        return float(str.replace('$', '').replace(',', ''))

    def remove_package_id(self, str) -> str:
        return re.sub(r'\(\d+\)', '', str).lower().strip()
        # return re.sub(r' \(\d+\)', '', str)
