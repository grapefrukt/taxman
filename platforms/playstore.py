import pandas as pd
from platforms.platform import *


class PlatformPlayStore(Platform):
    @property
    def name(self) -> str:
        return 'play-store'

    def download(self, month):
        pass

    def _parse(self, month):
        df = pd.DataFrame()

        # these are the columns we'll need, ignore everything else
        cols = ['Description', 'Product Title', 'Amount (Merchant Currency)']
        dtype = {'Description': str, 'Product Title': str, 'Amount (Merchant Currency)': float}

        # for some reason, the report is sometimes split into multiple files, check if any are present and concat them
        index = None
        while (self.check_month_present(month, index)):
            # if index is not None: print(f'multi file for {month} at {index}')
            df = pd.concat([df, pd.read_csv(self.month_to_path(month, index), usecols=cols, dtype=dtype)])
            if index is None:
                index = 0
            index += 1

        # the description column contains a unique id per transaction,
        # we group by that to get a sum for each transaction
        df = df.groupby('Description')
        df = df.agg({
            'Amount (Merchant Currency)': 'sum',
            'Product Title': 'first',
        })

        # after the groupby and agg we turn this back into a normal dataframe
        df = df.reset_index()

        # we're now done with the description column and can drop it
        df = df.drop(columns=['Description'])
        # each row represents one sale
        df['units'] = 1

        df = df.rename(columns={
            'Product Title': 'title',
            'Product Id': 'title',
            'Amount (Merchant Currency)': 'sek',
        })

        return ParseResult.OK, df
