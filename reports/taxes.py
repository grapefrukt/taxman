import pandas as pd
from reports.report import *


class ReportForTaxes(Report):
    
    def generate(self, months, platforms, df: pd.DataFrame) -> str:
        df = df.groupby(['platform', 'year', 'month', 'title'])
        df = df.agg({
            'units': 'sum',
            'sek': 'sum',
        })

        df = df.sort_values(['year', 'month', 'title'], ascending=True)
        df = df.reset_index()

        # figure out if this report has both google play pass and play store
        if self.has_double_google(platforms):
            platforms.remove('play-pass')
            platforms.remove('play-store')
            platforms.append('google')

        for platform in platforms:
            for month in months:
                # now, if we have both google platforms, use a special function that merges them
                if platform == 'google':
                    print(self.google(month, df))
                else:
                    print(self.default(platform, month, df))

    def modify_months(self, months, platforms):
        if self.has_double_google(platforms):
            print("report has both play pass and play store, prepending extra month!\n")
            months.insert(0, months[0].add_months(-1))
        return months

    def default(self, platform, month, df: pd.DataFrame, header:bool=True) -> str:
        out = ''
        
        if header:
            out += f'sales report for {platform} {month}\n\n'
            out += 'PER TITLE (including charges, fees, taxes, and refunds):\n\n'

        df = df.loc[
            (df['platform'] == platform) &
            (df['year'] == month.year) &
            (df['month'] == month.month)
            ]

        # drop any columns we don't need
        df = df[['title', 'units', 'sek']]

        # calculate a sum for the numeric columns (units/sek)
        # turn that into a dataframe (it was a series)
        df_sum = df.sum(numeric_only=True).to_frame().T
        # set the title of that row to something i can replace later
        df_sum['title'] = '¤'
        # and concat it with the other data
        df = pd.concat([df, df_sum], ignore_index=True)

        # convert the sek and units to the proper formats
        df['sek'] = df.apply(lambda row: self.format_currency(row['sek']), axis=1)
        df['units'] = df.apply(lambda row: self.format_units(row['units']), axis=1)

        # turn the dataframe into a string
        df_str = df.to_string(index=False)

        # now we replace that summary row marker with a newline to space it one line lower
        for line in df_str.splitlines():
            if '¤' in line:
                line = f'\n{line.replace('¤', ' ')}'
            out += line + '\n'

        out += '\n\n'
        
        return out

    def google(self, month, df: pd.DataFrame) -> str:
        offset_month = month.add_months(-1)

        out = ""
        out += f'sales report for play pass {offset_month} and play store {month}\n\n'
        out += 'PER TITLE (including charges, fees, taxes, and refunds):\n\n'

        out += 'play store\n'
        out += self.default('play-store', month, df, header=False)
        out += 'play pass\n'
        out += self.default('play-pass', offset_month, df, header=False)

        return out

    def has_double_google(self, platforms):
        return 'play-pass' in platforms and 'play-store' in platforms