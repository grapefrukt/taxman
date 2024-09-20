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

        # if it's not set up, we read in the payments table and bank statements table now, this will happen once per run
        if self.df_payments is None :
            # read the tsv and rename some columns
            self.df_payments = pd.read_csv(self.file_to_path('payments.tsv'), sep='\t', usecols=['Reporting Period', 'Payment Date', 'Net Payment'])
            self.df_payments = self.df_payments.rename(columns={
                'Reporting Period': 'month',
                'Payment Date': 'send date',
                'Net Payment': 'usd',
            })

            # convert some column datatypes to what we need
            self.df_payments['send date'] = pd.to_datetime(self.df_payments['send date'])
            self.df_payments['month'] = self.df_payments['month'].apply(self.format_date)
            self.df_payments['usd'] = self.df_payments['usd'].apply(self.strip_dollar_sign)

            # because months and payments do not match 1 to 1, we need to group by the send date
            # that will give us a sum that matches up with the bank statement entry, this is because 
            # some months will not reach the payment threshold and will not pay out until next month
            self.df_payments = self.df_payments.groupby(['send date'])
            # we summarize the usd column, the month column will be merged (with spaces) to contain all months it had payments for
            self.df_payments = self.df_payments.agg({'usd': 'sum', 'month' : ' '.join})
            # then we need to reset the index to turn this back into a regular dataframe
            self.df_payments = self.df_payments.reset_index()

            # now we read in the bank statement
            df_bank = pd.read_csv(self.file_to_path('bank_statement.tsv'), sep='\t')
            # and rename a column just to keep things less confusing
            df_bank = df_bank.rename(columns={'date': 'receive date'})
            # and convert this column to be a datetime column so we can search it easier later
            df_bank['receive date'] = pd.to_datetime(df_bank['receive date'])
            # and set the index because of reasons?
            df_bank.set_index('receive date', inplace=True)

            # this line searches the bank statement for the nearest payout (within limits) and returns the corresponding value in sek
            self.df_payments['sek'] = self.df_payments.apply(lambda row: self.find_in_bank_statement(row, df_bank), axis=1)

            # then, it's a simple matter of dividing the sek value with the usd value to get an exchange rate
            # this will be read later when converting that months payout to sek
            self.df_payments['exchange rate'] = self.df_payments['sek'] / self.df_payments['usd']


        df = pd.read_html(self.month_to_path(month))[0]

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

        exchange_rate = float(self.df_payments[self.df_payments['month'].str.contains(str(month))]['exchange rate'].iloc[0])
        df['sek'] = df['usd'] * exchange_rate

        return ParseResult.OK, df

    def strip_dollar_sign(self, str) -> float:
        return float(str.replace('$', '').replace(',', ''))

    def remove_package_id(self, str) -> str:
        return re.sub(r'\(\d+\)', '', str).lower().strip()

    def format_date(self, str) -> datetime:
        return datetime.strptime(str, '%B %Y').strftime('%Y-%m')

    def find_in_bank_statement(self, row, df_bank) :
        # convert the send date to be a datetime
        send_date = row['send date'].to_pydatetime()
        # find the index to the row in the bank statement data frame that is nearest our send date
        # this may not be close at all, depending on what data is in the bank statement table!
        iloc_idx = df_bank.index.get_indexer([row['send date']], method='nearest')
        # use that index to retrieve the actual row from the bank statement
        # then get the date and the sek value from that (i don't fully understand how this bit works tbh)
        receive_date = df_bank.index[iloc_idx][0].to_pydatetime()
        sek = df_bank.iloc[iloc_idx].iloc[0]['sek']

        # once we have the payment date, we can calculate a delta between the payment being sent and it being received
        delta = (receive_date - send_date).days

        #  do some sanity checks on this delta
        if abs(delta) > 10 :
            raise Exception(f"No received payment found for {send_date:%Y-%m-%d}, best candidate was {receive_date:%Y-%m-%d} and that's {delta} days away")
        if delta < 0 :
            raise Exception(f'Payment received before it was sent! sent on: {send_date:%Y-%m-%d}, received on: {receive_date:%Y-%m-%d}')

        #print(f"looking for {send_date:%Y-%m-%d}, found {receive_date:%Y-%m-%d}, delta: {delta}")

        return float(sek)
