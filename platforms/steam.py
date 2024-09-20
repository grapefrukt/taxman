import pandas as pd
from datetime import datetime
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

        df_payments = pd.read_csv(self.file_to_path('payments.tsv'), sep='\t', usecols=['Reporting Period', 'Payment Date', 'Net Payment'])
        df_payments = df_payments.rename(columns={
            'Reporting Period': 'month',
            'Payment Date': 'send_date',
            'Net Payment': 'usd',
        })

        df_payments['send_date'] = pd.to_datetime(df_payments['send_date'])
        df_payments['month'] = df_payments['month'].apply(self.format_date)
        df_payments['usd'] = df_payments['usd'].apply(self.strip_dollar_sign)
        df_payments.set_index('month', inplace=True)
        print(df_payments)

        df_bank = pd.read_csv(self.file_to_path('bank_statement.tsv'), sep='\t')
        df_bank = df_bank.rename(columns={'date': 'receive_date'})
        df_bank['receive_date'] = pd.to_datetime(df_bank['receive_date'])
        df_bank.set_index('receive_date', inplace=True)
        print(df_bank)

        df_payments['sek'] = df_payments.apply(lambda row: self.find_in_bank_statement(row, df_bank), axis=1)

        print(df_payments)

        return ParseResult.OK, df

    def strip_dollar_sign(self, str) -> float:
        return float(str.replace('$', '').replace(',', ''))

    def remove_package_id(self, str) -> str:
        return re.sub(r'\(\d+\)', '', str).lower().strip()

    def format_date(self, str) -> datetime:
        return datetime.strptime(str, '%B %Y').strftime('%Y-%m')

    def find_in_bank_statement(self, row, df_bank) :
        send_date = row['send_date'].to_pydatetime()
        iloc_idx = df_bank.index.get_indexer([row['send_date']], method='nearest')
        #print(f"index: {iloc_idx}")
        #print(f"result: {df_bank.index[iloc_idx]}")
        receive_date = df_bank.index[iloc_idx][0].to_pydatetime()
        sek = df_bank.iloc[iloc_idx].iloc[0]['sek']
        delta = (receive_date - send_date).days

        if abs(delta) > 20 :
            raise Exception(f"No received payment found for {send_date:%Y-%m-%d}, best candidate was {receive_date:%Y-%m-%d} and that's {delta} days away")
        if delta < 0 :
            raise Exception(f'Payment received before it was sent! sent on: {send_date:%Y-%m-%d}, received on: {receive_date:%Y-%m-%d}')

        print(f"looking for {send_date:%Y-%m-%d}, found {receive_date:%Y-%m-%d}, delta: {delta}")

        return sek
