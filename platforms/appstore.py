from io import StringIO
import pandas as pd
from platforms.platform import *


class PlatformAppStore(Platform):
    @property
    def name(self) -> str:
        return 'appstore'

    # app store always needs two files to get the numbers we need
    def check_month_present(self, month: TaxMonth, index=None) -> bool:
        if index is None:
            if not self.check_month_present(month, 'payment'):
                print("missing payment file")
            if not self.check_month_present(month, 'sales'):
                if not self.has_sales_directory(month):
                    print("missing both sales file and directory")
                    return False
            return True
        else:
            return super().check_month_present(month, index)

    def check_month_excluded(self, month: TaxMonth, index=None) -> bool:
        return super().check_month_excluded(month, 'payment')

    def download(self, month):
        pass

    def _parse(self, month):
        csv_payment = self.preprocess_payment(self.month_to_path(month, 'payment'))
        io_payment = StringIO(csv_payment)

        # because some fields have changed names, we need to read them all
        df_exchange = pd.read_csv(io_payment)

        # rename the fields to be shorter, here we merge the currency field into one (the one that was renamed in 2019)
        df_exchange = df_exchange.rename(columns={
            'Country or Region (Currency)': 'currency',
            'Region (Currency)': 'currency',
            'Territory (Currency)': 'currency',
            'Earned': 'earned',
            'Proceeds': 'sek',
        })

        # then, to make debugging easier, we drop everything except the columns we care about
        df_exchange = df_exchange.filter(['currency', 'earned', 'sek'])

        # print(df_exchange)

        # shorten the region/currency field to be just currency
        df_exchange['currency'] = df_exchange['currency'].apply(self.region_to_currency)

        # some currencies (usd) appear multiple times, idk if they use a slightly different exchange rate
        # or if it's rounding, for our purposes, we can sum these and use them as one and the same
        df_exchange = df_exchange.groupby('currency')
        df_exchange = df_exchange.agg({
            'earned': 'sum',
            'sek': 'sum',
        })

        # calculate the exchange rate per currency, this is why we loaded this data in the first place
        df_exchange['exchange rate'] = df_exchange['sek'] / df_exchange['earned']

        # some older data only comes in multi file format
        # luckily it's the same data just spread across separate files, so we can read them all in and
        # just skip the headers of the later ones and it'll parse just the same
        if self.has_sales_directory(month):
            csv_sales = ""
            drop_header = False
            for file in os.listdir(self.sales_directory(month)):
                csv_sales = csv_sales + self.preprocess_sales(f'{self.sales_directory(month)}/{file}', drop_header=drop_header)
                drop_header = True

        else:
            csv_sales = self.preprocess_sales(self.month_to_path(month, 'sales'))

        io_sales = StringIO(csv_sales)
        columns = [
            'Vendor Identifier',
            'Quantity',
            'Extended Partner Share',
            'Partner Share Currency']
        df_sales = pd.read_csv(io_sales, usecols=columns, sep='\t')

        # rename the fields to be shorter
        df_sales = df_sales.rename(columns={
            'Vendor Identifier': 'title',
            'Partner Share Currency': 'currency',
            'Extended Partner Share': 'earned',
            'Quantity': 'units',
        })

        # remap the game titles
        df_sales = df_sales.replace({'title': self.title_remap})

        # now we summarize the units and earnings per game per currency
        # we have to do it beforehand, because they may be cases where all sales for a currency were returned
        # in that case, the returned currency won't be in our lookup table and we'll have errors
        # this way, those transactions will zero out and we'll know it's okay that currency is missing
        df_sales = df_sales.groupby(['title', 'currency'])
        df_sales = df_sales.agg({
            'units': 'sum',
            'earned': 'sum',
        })
        df_sales.reset_index(inplace=True)

        # print(df_sales)

        # use the payout lookup to work out how much each game earned in each currency
        df_sales['sek'] = df_sales.apply(
            lambda row: self.exchange_rate(row, df_exchange), axis=1)

        # check if the game has any entries with non-zero sales that still made no money.
        # this happens if we don't have the exchange rate for that currency for this month.
        # that can happen if we sold one game in say, MXN, and another game was returned in MXN.
        # if those two cost the same, we will not be paid in MXN, thus not have an exchange rate
        # but we still need to work out what that particular sale was worth because it's on two
        # different games
        df_sales['sek'] = df_sales.apply(
            lambda row: self.fix_missing_exchange_rate(row, df_sales), axis=1)

        # then we collapse all the per-game-per-currency earnings down into just per game
        df_sales = df_sales.groupby(['title'])
        df_sales = df_sales.agg({
            'units': 'sum',
            'sek': 'sum',
        })

        # reset the index so we can merge with everything else later
        df_sales.reset_index(inplace=True)

        return ParseResult.OK, df_sales

    def exchange_rate(self, row, df_payout):
        # if something is sold in a currency and then all of it is returned
        # that currency will be in the sales table, but not in the payout table
        # (because that currency never got paid out)
        # it may also be that there's tax or something funky meaning had a negative pay out despite no sales
        # if the earned field is zero, we can safely return a zero exchange rate here
        if row['earned'] == 0:
            return 0

        if not row['currency'] in df_payout.index:
            print(f"missing exchange data for {row['currency']}, {row['earned']}")
            return 0

        # because this is an approximate value, we have to round it off here
        return round(row['earned'] * df_payout.loc[row['currency']]['exchange rate'], 2)

    def fix_missing_exchange_rate(self, row, df_sales):
        # if the game has not sold any units in this currency, we're good
        # if it already has a sek value, we're also good
        if row['units'] == 0 or row['sek'] != 0:
            return row['sek']

        # if we're not good, we summarize all the sales for this game for this month, number and revenue (in sek)
        df_sum = df_sales.loc[(df_sales['title'] == row['title']) & (
            df_sales['currency'] != row['currency'])]
        df_sum = df_sum.groupby('title')
        df_sum = df_sum.agg({'units': 'sum', 'sek': 'sum'})
        # then we get the first (and only row)
        row_sum = df_sum.iloc[0]
        # and calculate the average price of this game this month
        average_price = row_sum['sek'] / row_sum['units']

        # we can then use that to do an educated guess as to what this was worth
        return row['units'] * average_price

    def preprocess_payment(self, path) -> str:
        processed = ''
        line_count = -1
        with open(path, 'r', encoding='utf8') as file:
            for line in file:
                line_count += 1
                # skip the first two lines, they're not interesting
                if line_count < 2:
                    continue
                # some files are inexplicably tab separated, luckily it's easily fixed here
                line = line.replace('\t', ',')
                # once we reach an "empty" line, we bail
                # empty line is all commas and possibly some whitespace (always a newline)
                if line.replace(',', '').rstrip() == '':
                    break
                processed += line

        return processed

    def preprocess_sales(self, path, drop_header=False) -> str:
        processed = ''
        with open(path, 'r', encoding='utf8') as file:
            for line in file:
                if drop_header:
                    drop_header = False
                    continue
                # once we reach the line that starts with 'Total_Rows' we bail
                if 'Total_Rows' in line:
                    break
                processed += line

        return processed

    def sales_directory(self, month) -> str:
        return self.month_to_path(month, 'sales').replace(self.data_extension, '')

    def has_sales_directory(self, month) -> bool:
        return os.path.isdir(self.sales_directory(month))

    # the currency is in parenthesis at the end of the region, this function strips out just the currency abbreviation
    def region_to_currency(self, str) -> str:
        return str[-4:-1]
