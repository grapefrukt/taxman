from datetime import datetime
import pandas as pd
from platforms.platform import *


class PlatformPlayStore(Platform):
    @property
    def name(self) -> str:
        return 'play-store'

    def download(self, month):
        pass

    def _parse(self, month):
        df = pd.read_csv(self.month_to_path(month))

        # for some reason, the report is sometimes split into multiple files, check if any are present and concat them
        index = 1
        while (self.check_month_present(month, index)):
            print(f'multi file for {month} at {index}')
            df = pd.concat([df, pd.read_csv(self.month_to_path(month, index))])
            index += 1

        # get rid of all the columns we don't need
        # todo: update to use usecols instead
        cols = ['Description', 'Transaction Date', 'Product Title', 'Amount (Merchant Currency)']
        df = df.filter(cols)

        # the description column contains a unique id per transaction,
        # we group by that to get a sum for each transaction
        df = df.groupby('Description')
        df = df.agg({
            'Amount (Merchant Currency)': 'sum',
            'Product Title': 'first',
            'Transaction Date': 'first'
        })

        # after the groupby and agg we turn this back into a normal dataframe
        df = df.reset_index()

        # we're now done with the description column and can drop it
        df = df.drop(columns=['Description'])
        # each row represents one sale
        df['units'] = 1

        df['Transaction Date'] = df['Transaction Date'].apply(self.format_date)
        df = df.rename(columns={
            'Product Title': 'title',
            'Transaction Date': 'month',
            'Product Id': 'title',
            'Amount (Merchant Currency)': 'sek',
        })

        return ParseResult.OK, df

    def format_date(self, str) -> str:
        return datetime.strptime(str, '%b %d, %Y').strftime('%Y-%m')
