import pandas as pd
from platforms.platform import *


class PlatformPlayStore(Platform):
    @property
    def name(self) -> str:
        return 'play-store'

    # this function reads and prepares a months data as a dataframe, this is split out so i can read two months in the parse function below
    def __parse(self, month):
        df = pd.DataFrame()

        # these are the columns we'll need, ignore everything else
        cols = ['Description', 'Tax Type', 'Product Title', 'Amount (Merchant Currency)']
        dtype = {'Description': str,  'Tax Type': str, 'Product Title': str, 'Amount (Merchant Currency)': float}

        # for some reason, the report is sometimes split into multiple files, check if any are present and concat them
        index = None
        while (self.check_month_present(month, index)):
            # if index is not None: print(f'multi file for {month} at {index}')
            df = pd.concat([df, pd.read_csv(self.month_to_path(month, index), usecols=cols, dtype=dtype)])
            if index is None:
                index = 0
            index += 1

        #print(df.loc[df['Transaction Type'] == 'Tax'])
        df.loc[df['Tax Type'] == 'Taiwan Withholding Tax', 'Product Title'] = 'taiwan withholding tax'
        df.loc[df['Tax Type'] == 'Taiwan Withholding Tax', 'Description']   = 'taiwan withholding tax'
        df.loc[df['Tax Type'] == 'Brazil CIDE Withholding Tax', 'Product Title'] = 'brazil withholding tax'
        df.loc[df['Tax Type'] == 'Brazil CIDE Withholding Tax', 'Description']   = 'brazil withholding tax'
        df.loc[df['Tax Type'] == 'Brazil IRRF Withholding Tax', 'Product Title'] = 'brazil withholding tax'
        df.loc[df['Tax Type'] == 'Brazil IRRF Withholding Tax', 'Description']   = 'brazil withholding tax'
        #print(df.loc[df['Transaction Type'] == 'Tax'])

        # the description column contains a unique id per transaction,
        # we group by that to get a sum for each transaction
        df = df.groupby('Description')
        df = df.agg({
            'Amount (Merchant Currency)': 'sum',
            'Product Title': 'first',
        })

        # after the groupby and agg we turn this back into a normal dataframe
        df = df.reset_index()

        return df

    def _parse(self, month):
        df = self.__parse(month)

        # because google hates me the taiwan witholding tax for any given month is processed 
        # in the middle of the following month, before the payment is made
        # this means the data for that tax lands on the month after, so we need both month 0 and +1 to calculate a correct payout
        # ideally, i'd only do this for the tax reports, since it's not super relevant for revshare
        next_month = month.add_months(1);
        if self.check_month_present(next_month):
            df_next = self.__parse(month.add_months(1))
            df.drop(df[df['Description'] == 'taiwan withholding tax'].index, inplace=True)
            df_next.drop(df_next[df_next['Description'] != 'taiwan withholding tax'].index, inplace=True)

            df = pd.concat([df, df_next])
        else :
            print(f'{self.name}: next month is missing for {month}, will likely have incorrect values for taiwan withholding tax')
                
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
