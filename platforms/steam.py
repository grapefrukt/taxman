import pandas as pd
from datetime import datetime
from platforms.platform import *
import re


class PlatformSteam(Platform):
    def __init__(self, config):
        super().__init__(config)
        self.df_payments = None

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

        if self.df_payments is None :
            self.df_payments = pd.read_csv(self.file_to_path('payments.tsv'), sep='\t', usecols=['Reporting Period', 'Payment Date', 'Net Payment'])
            self.df_payments = self.df_payments.rename(columns={
                'Reporting Period': 'month',
                'Payment Date': 'send date',
                'Net Payment': 'usd',
            })

            self.df_payments['send date'] = pd.to_datetime(self.df_payments['send date'])
            self.df_payments['month'] = self.df_payments['month'].apply(self.format_date)
            self.df_payments['usd'] = self.df_payments['usd'].apply(self.strip_dollar_sign)

            #self.df_payments.groupby('send date')
            #self.df_payments = self.df_payments.agg({
            #    'month': 'first',
            #    'usd': 'sum',
            #})

            self.df_payments.set_index('month', inplace=True)

            df_bank = pd.read_csv(self.file_to_path('bank_statement.tsv'), sep='\t')
            df_bank = df_bank.rename(columns={'date': 'receive date'})
            df_bank['receive date'] = pd.to_datetime(df_bank['receive date'])
            df_bank.set_index('receive date', inplace=True)

            self.df_payments['sek'] = self.df_payments.apply(lambda row: self.find_in_bank_statement(row, df_bank), axis=1)
            self.df_payments['exchange rate'] = self.df_payments['sek'] / self.df_payments['usd']

        #print(df)
        #print(self.df_payments)

        exchange_rate = self.df_payments.loc[str(month)]['exchange rate']
        #print(exchange_rate)

        df['sek'] = df['usd'] * exchange_rate

        return ParseResult.OK, df

    def strip_dollar_sign(self, str) -> float:
        return float(str.replace('$', '').replace(',', ''))

    def remove_package_id(self, str) -> str:
        return re.sub(r'\(\d+\)', '', str).lower().strip()

    def format_date(self, str) -> datetime:
        return datetime.strptime(str, '%B %Y').strftime('%Y-%m')

    def find_in_bank_statement(self, row, df_bank) :
        send_date = row['send date'].to_pydatetime()
        iloc_idx = df_bank.index.get_indexer([row['send date']], method='nearest')
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

        return float(sek)
